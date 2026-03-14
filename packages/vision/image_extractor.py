"""
AI image extraction pipeline.

Loads an image (or keyframe), calls the model router with the image_v1 prompt,
validates the output against ImageExtractionOutput schema, and persists all
typed results to the DB.

Entry points:
  extract_asset(asset_id, session, provider)   — single asset
  extract_all_pending(provider, limit)          — batch
"""
from __future__ import annotations

import json
import logging
import re
import sys
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

from PIL import Image
from pydantic import ValidationError
from sqlalchemy.orm import Session

# DB models
sys.path.insert(0, str(Path(__file__).parents[2] / "db"))
from models import (  # noqa: E402
    Asset, ExtractionRun,
    OcrDocument, ObjectDetection as DBObjectDetection,
    SceneSummary as DBSceneSummary, PlaceCandidate as DBPlaceCandidate,
)
from session import get_session  # noqa: E402
from sqlalchemy import delete as sa_delete  # noqa: E402

# Model router + schemas (same package dir pattern as other packages)
sys.path.insert(0, str(Path(__file__).parents[2] / "models"))
from router import get_provider  # noqa: E402
from provider import ModelProvider  # noqa: E402
from schemas import ImageExtractionOutput, SCHEMA_VERSION  # noqa: E402

logger = logging.getLogger(__name__)

# Gemini 3.1 Flash-Lite pricing (per 1M tokens)
_COST_PER_M_IN = 0.25   # text/image input
_COST_PER_M_OUT = 1.50  # output + thinking tokens


def _calculate_cost(tokens_in: int, tokens_out: int) -> float:
    return (tokens_in * _COST_PER_M_IN + tokens_out * _COST_PER_M_OUT) / 1_000_000

# Formats PIL can open natively
PIL_IMAGE_EXT = {
    ".jpg", ".jpeg", ".png", ".tiff", ".tif", ".heic", ".heif",
    ".webp", ".bmp", ".avif",
}

# RAW formats — require thumbnail fallback
RAW_IMAGE_EXT = {
    ".raw", ".cr2", ".cr3", ".nef", ".nrw",
    ".arw", ".srf", ".sr2",
    ".orf", ".rw2", ".dng", ".raf", ".pef", ".x3f", ".mrw",
}

SUPPORTED_IMAGE_EXT = PIL_IMAGE_EXT | RAW_IMAGE_EXT

PROMPT_PATH = Path(__file__).parents[2] / "prompts" / "image_v1.txt"

# Resend at most this many bytes to Gemini (images are downscaled to fit)
MAX_GEMINI_PX = 1200
MAX_ORIGINAL_BYTES = 8 * 1024 * 1024  # 8 MB — above this, prefer the thumbnail
ANALYSIS_THUMB_WIDTH = 1200  # preferred thumbnail size for AI analysis


def _load_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def _pil_to_jpeg_bytes(path: Path, max_px: int = MAX_GEMINI_PX) -> bytes:
    """Open a PIL-readable image, downscale if needed, return JPEG bytes."""
    with Image.open(path) as img:
        img = img.convert("RGB")
        w, h = img.size
        if max(w, h) > max_px:
            ratio = max_px / max(w, h)
            img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)
        buf = BytesIO()
        img.save(buf, "JPEG", quality=85)
        return buf.getvalue()


def _resolve_image_bytes(asset: Asset, path: Path) -> tuple[bytes, str]:
    """
    Return (jpeg_bytes, mime_type) for Gemini.

    Strategy:
    - RAW files or originals > MAX_ORIGINAL_BYTES → use pre-generated thumbnail
    - Otherwise → decode with PIL and downscale to MAX_GEMINI_PX
    Falls back to thumbnail whenever PIL fails.
    """
    ext = path.suffix.lower()
    is_raw = ext in RAW_IMAGE_EXT
    is_large = path.stat().st_size > MAX_ORIGINAL_BYTES

    if not is_raw and not is_large:
        # Happy path: PIL-readable, reasonably sized
        try:
            return _pil_to_jpeg_bytes(path), "image/jpeg"
        except Exception as exc:
            logger.warning("PIL failed on %s (%s), falling back to thumbnail", path.name, exc)

    # Fall back to the pre-generated thumbnail (already a JPEG) — prefer 1200px
    if asset.thumbnails:
        sorted_thumbs = sorted(asset.thumbnails, key=lambda t: t.width)
        # Prefer the 1200px analysis thumbnail; settle for the largest available
        preferred = next((t for t in sorted_thumbs if t.width >= ANALYSIS_THUMB_WIDTH), None)
        thumb = preferred or sorted_thumbs[-1]
        thumb_path = Path(thumb.path)
        if thumb_path.exists():
            logger.info("Using thumbnail (%dpx) for %s (raw=%s large=%s)", thumb.width, path.name, is_raw, is_large)
            return thumb_path.read_bytes(), "image/jpeg"

    # No thumbnail — try PIL anyway (last resort)
    return _pil_to_jpeg_bytes(path), "image/jpeg"


def _parse_json_from_response(text: str) -> dict:
    """Strip markdown fences and parse JSON."""
    text = text.strip()
    # Remove ```json ... ``` fences
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\s*```$", "", text, flags=re.MULTILINE)
    return json.loads(text.strip())


def _persist_results(
    session: Session,
    asset: Asset,
    run: ExtractionRun,
    output: ImageExtractionOutput,
) -> None:
    # Delete any previous extraction data for this asset (upsert semantics)
    session.execute(sa_delete(OcrDocument).where(OcrDocument.asset_id == asset.id))
    session.execute(sa_delete(DBSceneSummary).where(DBSceneSummary.asset_id == asset.id))
    session.execute(sa_delete(DBObjectDetection).where(DBObjectDetection.asset_id == asset.id))
    session.execute(sa_delete(DBPlaceCandidate).where(DBPlaceCandidate.asset_id == asset.id))

    # OCR
    if output.ocr_text:
        session.add(OcrDocument(
            asset_id=asset.id,
            extraction_run_id=run.id,
            full_text=output.ocr_text,
            confidence=output.confidence_overall,
        ))

    # Scene
    s = output.scene
    session.add(DBSceneSummary(
        asset_id=asset.id,
        extraction_run_id=run.id,
        scene_type=s.setting,
        time_of_day=s.lighting,
        weather=s.weather,
        description=s.description,
        confidence=output.confidence_overall,
        raw=output.model_dump(),
    ))

    # Objects
    for obj in output.objects:
        attrs: dict = {}
        if obj.bbox:
            attrs["bbox"] = obj.bbox.model_dump()
        attrs["count"] = obj.count
        session.add(DBObjectDetection(
            asset_id=asset.id,
            extraction_run_id=run.id,
            label=obj.label,
            confidence=obj.confidence,
            attributes=attrs or None,
        ))

    # Place candidates
    for pc in output.place_candidates:
        session.add(DBPlaceCandidate(
            asset_id=asset.id,
            extraction_run_id=run.id,
            name=pc.name,
            country=pc.country,
            region=pc.region,
            place_type=pc.place_type,
            confidence=pc.confidence,
            source="ai",
            raw=pc.model_dump(),
        ))


def extract_asset(
    asset: Asset,
    session: Session,
    provider: ModelProvider,
) -> ExtractionRun:
    """Run AI extraction for a single asset. Creates an ExtractionRun record."""
    run = ExtractionRun(
        asset_id=asset.id,
        run_type="image",
        model_provider=provider.provider_name,
        model_name=provider.model_name,
        schema_version=SCHEMA_VERSION,
        prompt_version="image_v1",
        status="running",
        started_at=datetime.now(timezone.utc),
    )
    session.add(run)
    session.flush()

    path = Path(asset.canonical_path)
    if not path.exists():
        run.status = "failed"
        run.error_message = "File not found on disk"
        return run

    try:
        img_bytes, mime = _resolve_image_bytes(asset, path)
        prompt = _load_prompt()
        result = provider.generate(prompt, img_bytes, mime)
        raw_json = _parse_json_from_response(result.text)
        output = ImageExtractionOutput.model_validate(raw_json)

        run.raw_output = raw_json
        run.tokens_in = result.tokens_in
        run.tokens_out = result.tokens_out
        run.cost_usd = _calculate_cost(result.tokens_in, result.tokens_out)
        run.status = "done"
        run.finished_at = datetime.now(timezone.utc)

        _persist_results(session, asset, run, output)

    except ValidationError as exc:
        run.status = "failed"
        run.error_message = f"Schema validation failed: {exc.error_count()} error(s)"
        logger.warning("Extraction schema error for %s: %s", asset.id, exc)
    except Exception as exc:
        run.status = "failed"
        run.error_message = str(exc)
        logger.exception("Extraction failed for %s", asset.id)

    return run


def extract_all_pending(
    model_provider: str = "gemini",
    model_name: str = "gemini-3.1-flash-lite-preview",
    limit: int = 50,
) -> dict[str, int]:
    """Batch-extract all assets that haven't been extracted yet."""
    stats = {"processed": 0, "failed": 0, "skipped": 0}

    provider = get_provider(model_provider, model_name)
    prompt = _load_prompt()  # validate prompt loads before touching DB

    with get_session() as session:
        # Find assets with no successful extraction run
        from sqlalchemy import select

        done_subq = (
            select(ExtractionRun.asset_id)
            .where(ExtractionRun.status == "done")
            .scalar_subquery()
        )
        assets = (
            session.query(Asset)
            .filter(
                Asset.is_missing == False,  # noqa: E712
                Asset.media_type == "photo",
                ~Asset.id.in_(done_subq),
            )
            .limit(limit)
            .all()
        )

        for asset in assets:
            ext = Path(asset.canonical_path).suffix.lower()
            if ext not in SUPPORTED_IMAGE_EXT:
                stats["skipped"] += 1
                continue

            run = extract_asset(asset, session, provider)
            if run.status == "done":
                stats["processed"] += 1
            else:
                stats["failed"] += 1

    return stats

