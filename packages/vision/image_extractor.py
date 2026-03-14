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
import platform
import re
import sys
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Callable

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
APPLE_IMAGE_EXT = {".heic", ".heif"}

SUPPORTED_IMAGE_EXT = PIL_IMAGE_EXT | RAW_IMAGE_EXT

PROMPT_PATH = Path(__file__).parents[2] / "prompts" / "image_v1.txt"

# Resend at most this many bytes to Gemini (images are downscaled to fit)
MAX_GEMINI_PX = 1200
MAX_ORIGINAL_BYTES = 8 * 1024 * 1024  # 8 MB — above this, prefer the thumbnail
ANALYSIS_THUMB_WIDTH = 1200  # preferred thumbnail size for AI analysis
DEFAULT_MAX_OUTPUT_TOKENS = None
AI_DEBUG_DIR = Path(__file__).parents[2] / "var" / "ai_debug"


def _load_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def _write_ai_debug_dump(
    asset: Asset,
    *,
    stage: str,
    raw_text: str,
    parsed_json: dict | None = None,
    error_message: str | None = None,
) -> None:
    try:
        AI_DEBUG_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        payload = {
            "asset_id": asset.id,
            "filename": asset.filename,
            "canonical_path": asset.canonical_path,
            "stage": stage,
            "error_message": error_message,
            "raw_text": raw_text,
            "parsed_json": parsed_json,
        }
        target = AI_DEBUG_DIR / f"{stamp}_{asset.id}_{stage}.json"
        target.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info("Wrote AI debug dump for %s to %s", asset.filename, target)
    except Exception:
        logger.exception("Failed to write AI debug dump for %s", asset.filename)


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


def _apple_to_jpeg_bytes(path: Path, max_px: int = MAX_GEMINI_PX) -> bytes:
    with NamedTemporaryFile(suffix=".jpg") as tmp:
        subprocess = __import__("subprocess")
        subprocess.run(
            ["sips", "-Z", str(max_px), "-s", "format", "jpeg", str(path), "--out", tmp.name],
            capture_output=True,
            timeout=60,
            check=True,
        )
        return Path(tmp.name).read_bytes()


def _resolve_image_bytes(asset: Asset, path: Path, max_px: int = MAX_GEMINI_PX) -> tuple[bytes, str]:
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

    if ext in APPLE_IMAGE_EXT and platform.system() == "Darwin":
        try:
            return _apple_to_jpeg_bytes(path, max_px=max_px), "image/jpeg"
        except Exception as exc:
            logger.warning("sips failed on %s (%s), falling back", path.name, exc)

    if not is_raw and not is_large:
        # Happy path: PIL-readable, reasonably sized
        try:
            return _pil_to_jpeg_bytes(path, max_px=max_px), "image/jpeg"
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
    return _pil_to_jpeg_bytes(path, max_px=max_px), "image/jpeg"


def _parse_json_from_response(text: str) -> dict:
    """Strip markdown fences and parse JSON."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\s*```$", "", text, flags=re.MULTILINE)
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start:end + 1]
    return _load_json_with_repair(text.strip())


def _load_json_with_repair(text: str) -> dict:
    candidate = text
    for step in range(8):
        try:
            return json.loads(candidate)
        except json.JSONDecodeError as exc:
            if step == 0:
                candidate = _repair_json_like_text(candidate)
                continue
            repaired = _repair_json_at_error(candidate, exc)
            if repaired == candidate:
                repaired = _repair_json_at_line(candidate, exc)
            if repaired == candidate:
                raise
            candidate = repaired
    return json.loads(candidate)


def _repair_json_like_text(text: str) -> str:
    """Repair the most common model JSON mistakes before a second parse attempt."""
    out: list[str] = []
    in_string = False
    escape = False

    for i, char in enumerate(text):
        if escape:
            out.append(char)
            escape = False
            continue

        if char == "\\":
            out.append(char)
            escape = True
            continue

        if char == '"':
            if in_string:
                next_sig = _next_significant_char(text, i + 1)
                if next_sig in {",", "}", "]", ":"} or next_sig is None:
                    in_string = False
                    out.append(char)
                else:
                    out.append('\\"')
                continue
            in_string = True
            out.append(char)
            continue

        if in_string and char in ("\n", "\r"):
            out.append("\\n")
            continue

        out.append(char)

    repaired = "".join(out)
    repaired = re.sub(r",(\s*[}\]])", r"\1", repaired)
    return repaired


def _repair_json_at_error(text: str, exc: json.JSONDecodeError) -> str:
    pos = max(0, min(exc.pos, len(text)))
    prev_index = _prev_significant_index(text, pos - 1)
    next_index = _next_significant_index(text, pos)
    prev_char = text[prev_index] if prev_index is not None else None
    next_char = text[next_index] if next_index is not None else None
    message = exc.msg.lower()

    if "expecting ',' delimiter" in message:
        if _should_insert_comma(prev_char, next_char):
            return text[:pos] + "," + text[pos:]
        if next_char in ("\n", "\r"):
            return text[:next_index] + "\\n" + text[next_index + 1:]

    if "unterminated string" in message or "invalid control character" in message:
        newline_index = _find_next_newline(text, pos)
        if newline_index is not None:
            return text[:newline_index] + "\\n" + text[newline_index + 1:]

    if "expecting property name enclosed in double quotes" in message and next_char in ("}", "]"):
        return text[:prev_index + 1] + text[next_index:]

    return text


def _repair_json_at_line(text: str, exc: json.JSONDecodeError) -> str:
    lines = text.splitlines()
    line_index = max(0, min(exc.lineno - 1, len(lines) - 1))
    current = lines[line_index].lstrip() if lines else ""
    if not current:
        return text

    if current.startswith(('"', "{", "[")):
        prev_index = _previous_non_empty_line(lines, line_index - 1)
        if prev_index is None:
            return text
        previous = lines[prev_index].rstrip()
        if previous and not previous.endswith((",", "{", "[", ":")):
            lines[prev_index] = f"{previous},"
            return "\n".join(lines)
    return text


def _should_insert_comma(prev_char: str | None, next_char: str | None) -> bool:
    if prev_char is None or next_char is None:
        return False
    prev_ok = prev_char in {'"', "}", "]"} or prev_char.isdigit() or prev_char in {"e", "E", "l"}
    next_ok = next_char in {'"', "{", "["} or next_char.isalpha()
    return prev_ok and next_ok


def _previous_non_empty_line(lines: list[str], start: int) -> int | None:
    for index in range(start, -1, -1):
        if lines[index].strip():
            return index
    return None


def _prev_significant_index(text: str, start: int) -> int | None:
    for index in range(start, -1, -1):
        if not text[index].isspace():
            return index
    return None


def _next_significant_index(text: str, start: int) -> int | None:
    for index in range(max(0, start), len(text)):
        if not text[index].isspace():
            return index
    return None


def _find_next_newline(text: str, start: int) -> int | None:
    for index in range(max(0, start), len(text)):
        if text[index] in ("\n", "\r"):
            return index
    return None


def _next_significant_char(text: str, start: int) -> str | None:
    for char in text[start:]:
        if not char.isspace():
            return char
    return None


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
        if obj.color:
            attrs["color"] = obj.color
        if obj.details:
            attrs["details"] = obj.details
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
    *,
    max_px: int = MAX_GEMINI_PX,
    max_output_tokens: int | None = DEFAULT_MAX_OUTPUT_TOKENS,
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

    raw_text = ""
    try:
        img_bytes, mime = _resolve_image_bytes(asset, path, max_px=max_px)
        prompt = _load_prompt()
        effective_max_output_tokens = None if not max_output_tokens or max_output_tokens <= 0 else max_output_tokens
        result = provider.generate(prompt, img_bytes, mime, max_output_tokens=effective_max_output_tokens)
        raw_text = result.text or ""
        raw_json = _parse_json_from_response(result.text)
        output = ImageExtractionOutput.model_validate(raw_json)
        _write_ai_debug_dump(asset, stage="done", raw_text=raw_text, parsed_json=raw_json)

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
        _write_ai_debug_dump(asset, stage="schema_failed", raw_text=raw_text, error_message=str(exc))
        if raw_text:
            run.raw_output = _failure_debug_payload(raw_text, str(exc), "schema")
        run.finished_at = datetime.now(timezone.utc)
        logger.warning("Extraction schema error for %s: %s", asset.id, exc)
    except Exception as exc:
        run.status = "failed"
        run.error_message = _summarize_parse_error(str(exc), raw_text)
        _write_ai_debug_dump(asset, stage="parse_failed", raw_text=raw_text, error_message=str(exc))
        if raw_text:
            debug_stage = "truncated" if _looks_truncated_response(raw_text) else "parse"
            run.raw_output = _failure_debug_payload(raw_text, str(exc), debug_stage)
        run.finished_at = datetime.now(timezone.utc)
        logger.exception("Extraction failed for %s", asset.id)

    return run


def extract_all_pending(
    model_provider: str = "gemini",
    model_name: str = "gemini-3.1-flash-lite-preview",
    limit: int = 50,
    max_px: int = MAX_GEMINI_PX,
    max_output_tokens: int | None = DEFAULT_MAX_OUTPUT_TOKENS,
    folder_path: str | None = None,
    should_cancel: Callable[[], bool] | None = None,
) -> dict[str, int]:
    """Batch-extract all assets that haven't been extracted yet."""
    stats = {"processed": 0, "failed": 0, "skipped": 0, "cancelled": 0}
    failure_examples: list[str] = []

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
        query = (
            session.query(Asset)
            .filter(
                Asset.is_missing == False,  # noqa: E712
                Asset.media_type == "photo",
                ~Asset.id.in_(done_subq),
            )
        )
        if folder_path:
            query = query.filter(
                (Asset.canonical_path == folder_path) | (Asset.canonical_path.like(f"{folder_path}/%"))
            )
        assets = query.limit(limit).all()

        for asset in assets:
            if should_cancel and should_cancel():
                stats["cancelled"] = 1
                break
            ext = Path(asset.canonical_path).suffix.lower()
            if ext not in SUPPORTED_IMAGE_EXT:
                stats["skipped"] += 1
                continue

            run = extract_asset(asset, session, provider, max_px=max_px, max_output_tokens=max_output_tokens)
            if run.status == "done":
                stats["processed"] += 1
            else:
                stats["failed"] += 1
                if run.error_message and len(failure_examples) < 3:
                    failure_examples.append(f"{asset.filename}: {run.error_message}")

    if failure_examples:
        stats["failure_examples"] = failure_examples
    return stats


def _summarize_parse_error(message: str, raw_text: str = "") -> str:
    if raw_text and _looks_truncated_response(raw_text):
        return "AI response was cut off before the JSON finished. Try a higher output token limit."
    return message[:260]


def _looks_truncated_response(raw_text: str) -> bool:
    if not raw_text:
        return False
    stripped = raw_text.rstrip()
    if stripped.count("{") > stripped.count("}"):
        return True
    if stripped.count("[") > stripped.count("]"):
        return True
    if stripped.count('"') % 2 == 1:
        return True
    return stripped[-1] not in ("}", "]", '"')


def _failure_debug_payload(raw_text: str, error_message: str, stage: str) -> dict:
    return {
        "debug_stage": stage,
        "debug_error": error_message[:260],
        "debug_excerpt": _debug_excerpt(raw_text),
    }


def _debug_excerpt(raw_text: str, max_len: int = 800) -> str:
    compact = raw_text.replace("\r", "\\r").replace("\n", "\\n\n")
    return compact[:max_len]
