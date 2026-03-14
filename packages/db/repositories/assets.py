"""
Asset repository — CRUD operations for the asset catalog.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy import Text, cast, exists, or_, select, update
from sqlalchemy.orm import Session, selectinload

# Add db package to path for sibling import
import sys
sys.path.insert(0, str(Path(__file__).parents[2] / "db"))

from models import (  # noqa: E402
    Asset,
    AssetHash,
    AssetLocation,
    AssetTemporal,
    ExtractionRun,
    ObjectDetection,
    OcrDocument,
    PlaceCandidate,
    SceneSummary,
)


SUPPORTED_PHOTO_EXTS = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".tiff", ".tif", ".webp", ".bmp", ".gif", ".raw", ".cr2", ".cr3", ".nef", ".arw", ".dng"}
SUPPORTED_VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv", ".m4v", ".mts", ".m2ts", ".3gp", ".wmv"}


def get_media_type(path: Path) -> Optional[str]:
    ext = path.suffix.lower()
    if ext in SUPPORTED_PHOTO_EXTS:
        return "photo"
    if ext in SUPPORTED_VIDEO_EXTS:
        return "video"
    return None


def upsert_asset(session: Session, canonical_path: str, source_root: str) -> Asset:
    """Insert or update an asset record. Returns the asset."""
    path = Path(canonical_path)
    existing = session.scalar(select(Asset).where(Asset.canonical_path == canonical_path))

    if existing:
        existing.last_seen_at = datetime.now(timezone.utc)
        existing.is_missing = False
        existing.file_size_bytes = path.stat().st_size if path.exists() else existing.file_size_bytes
        return existing

    media_type = get_media_type(path)
    if not media_type:
        raise ValueError(f"Unsupported file type: {path.suffix}")

    asset = Asset(
        canonical_path=canonical_path,
        filename=path.name,
        extension=path.suffix.lower(),
        media_type=media_type,
        file_size_bytes=path.stat().st_size if path.exists() else None,
        source_root=source_root,
    )
    session.add(asset)
    return asset


def mark_missing(session: Session, source_root: str, seen_paths: set[str]) -> int:
    """Mark assets from source_root that weren't seen in this scan as missing."""
    result = session.execute(
        update(Asset)
        .where(Asset.source_root == source_root, ~Asset.canonical_path.in_(seen_paths))
        .values(is_missing=True)
        .returning(Asset.id)
    )
    return len(result.fetchall())


def get_asset_by_id(session: Session, asset_id: str) -> Optional[Asset]:
    return session.get(Asset, asset_id)


def _apply_asset_filters(
    q,
    *,
    media_type: Optional[str] = None,
    search: Optional[str] = None,
    ai_text: Optional[str] = None,
    scene: Optional[str] = None,
    place: Optional[str] = None,
    object_label: Optional[str] = None,
    folder: Optional[str] = None,
    has_thumbnail: Optional[bool] = None,
    has_ocr: Optional[bool] = None,
    has_gps: Optional[bool] = None,
    has_ai: Optional[bool] = None,
    review_bucket: Optional[str] = None,
):
    q = select(Asset).where(Asset.is_missing == False)  # noqa: E712
    if media_type:
        q = q.where(Asset.media_type == media_type)

    if folder:
        normalized = folder.strip().strip("/")
        q = q.where(Asset.canonical_path.ilike(f"%/{normalized}/%"))

    if has_thumbnail is True:
        q = q.where(
            or_(
                Asset.thumbnails.any(),
                Asset.keyframes.any(),
            )
        )

    if has_ocr is True:
        q = q.where(
            exists(
                select(OcrDocument.id).where(
                    OcrDocument.asset_id == Asset.id,
                    OcrDocument.full_text.is_not(None),
                    OcrDocument.full_text != "",
                )
            )
        )

    if has_gps is True:
        q = q.where(
            exists(select(AssetLocation.id).where(AssetLocation.asset_id == Asset.id))
        )

    if has_ai is True:
        q = q.where(
            or_(
                exists(select(SceneSummary.id).where(SceneSummary.asset_id == Asset.id)),
                exists(select(ObjectDetection.id).where(ObjectDetection.asset_id == Asset.id)),
                exists(select(PlaceCandidate.id).where(PlaceCandidate.asset_id == Asset.id)),
            )
        )

    if search and search.strip():
        term = search.strip()
        pattern = f"%{term}%"
        q = q.where(
            or_(
                Asset.filename.ilike(pattern),
                Asset.canonical_path.ilike(pattern),
                exists(
                    select(OcrDocument.id).where(
                        OcrDocument.asset_id == Asset.id,
                        OcrDocument.full_text.ilike(pattern),
                    )
                ),
                exists(
                    select(SceneSummary.id).where(
                        SceneSummary.asset_id == Asset.id,
                        or_(
                            SceneSummary.scene_type.ilike(pattern),
                            SceneSummary.setting.ilike(pattern),
                            SceneSummary.time_of_day.ilike(pattern),
                            SceneSummary.weather.ilike(pattern),
                            SceneSummary.description.ilike(pattern),
                        ),
                    )
                ),
                exists(
                    select(ObjectDetection.id).where(
                        ObjectDetection.asset_id == Asset.id,
                        ObjectDetection.label.ilike(pattern),
                    )
                ),
                exists(
                    select(PlaceCandidate.id).where(
                        PlaceCandidate.asset_id == Asset.id,
                        or_(
                            PlaceCandidate.name.ilike(pattern),
                            PlaceCandidate.country.ilike(pattern),
                            PlaceCandidate.region.ilike(pattern),
                            PlaceCandidate.place_type.ilike(pattern),
                        ),
                    )
                ),
            )
        )

    if ai_text and ai_text.strip():
        pattern = f"%{ai_text.strip()}%"
        q = q.where(
            exists(
                select(ExtractionRun.id).where(
                    ExtractionRun.asset_id == Asset.id,
                    or_(
                        cast(ExtractionRun.raw_output, Text).ilike(pattern),
                        ExtractionRun.error_message.ilike(pattern),
                    ),
                )
            )
        )

    if scene and scene.strip():
        pattern = f"%{scene.strip()}%"
        q = q.where(
            exists(
                select(SceneSummary.id).where(
                    SceneSummary.asset_id == Asset.id,
                    or_(
                        SceneSummary.scene_type.ilike(pattern),
                        SceneSummary.setting.ilike(pattern),
                        SceneSummary.time_of_day.ilike(pattern),
                        SceneSummary.weather.ilike(pattern),
                        SceneSummary.description.ilike(pattern),
                    ),
                )
            )
        )

    if place and place.strip():
        pattern = f"%{place.strip()}%"
        q = q.where(
            exists(
                select(PlaceCandidate.id).where(
                    PlaceCandidate.asset_id == Asset.id,
                    or_(
                        PlaceCandidate.name.ilike(pattern),
                        PlaceCandidate.country.ilike(pattern),
                        PlaceCandidate.region.ilike(pattern),
                        PlaceCandidate.place_type.ilike(pattern),
                    ),
                )
            )
        )

    if object_label and object_label.strip():
        pattern = f"%{object_label.strip()}%"
        q = q.where(
            exists(
                select(ObjectDetection.id).where(
                    ObjectDetection.asset_id == Asset.id,
                    ObjectDetection.label.ilike(pattern),
                )
            )
        )

    if review_bucket == "needs-extraction":
        q = q.where(
            ~exists(
                select(ExtractionRun.id).where(
                    ExtractionRun.asset_id == Asset.id,
                    ExtractionRun.status == "done",
                )
            )
        )
    elif review_bucket == "timestamp-conflict":
        q = q.where(
            exists(
                select(AssetTemporal.id).where(
                    AssetTemporal.asset_id == Asset.id,
                    AssetTemporal.has_conflict == True,  # noqa: E712
                )
            )
        )
    elif review_bucket == "low-confidence":
        q = q.where(
            exists(
                select(SceneSummary.id).where(
                    SceneSummary.asset_id == Asset.id,
                    SceneSummary.confidence.is_not(None),
                    SceneSummary.confidence < 0.72,
                )
            )
        )
    elif review_bucket == "location-unverified":
        q = q.where(
            exists(select(AssetLocation.id).where(AssetLocation.asset_id == Asset.id)),
            ~exists(select(PlaceCandidate.id).where(PlaceCandidate.asset_id == Asset.id)),
        )
    return q


def list_assets(
    session: Session,
    *,
    media_type: Optional[str] = None,
    search: Optional[str] = None,
    ai_text: Optional[str] = None,
    scene: Optional[str] = None,
    place: Optional[str] = None,
    object_label: Optional[str] = None,
    folder: Optional[str] = None,
    has_thumbnail: Optional[bool] = None,
    has_ocr: Optional[bool] = None,
    has_gps: Optional[bool] = None,
    has_ai: Optional[bool] = None,
    review_bucket: Optional[str] = None,
    page: int = 1,
    page_size: int = 48,
) -> tuple[list[Asset], int]:
    q = _apply_asset_filters(
        select(Asset),
        media_type=media_type,
        search=search,
        ai_text=ai_text,
        scene=scene,
        place=place,
        object_label=object_label,
        folder=folder,
        has_thumbnail=has_thumbnail,
        has_ocr=has_ocr,
        has_gps=has_gps,
        has_ai=has_ai,
        review_bucket=review_bucket,
    )

    # Count before pagination
    from sqlalchemy import func as sa_func
    count_q = select(sa_func.count()).select_from(q.subquery())
    total = session.scalar(count_q) or 0

    q = (
        q.options(
            selectinload(Asset.temporal),
            selectinload(Asset.location),
            selectinload(Asset.media_info),
            selectinload(Asset.thumbnails),
            selectinload(Asset.keyframes),
            selectinload(Asset.extraction_runs).selectinload(ExtractionRun.ocr_documents),
            selectinload(Asset.extraction_runs).selectinload(ExtractionRun.scene_summaries),
            selectinload(Asset.extraction_runs).selectinload(ExtractionRun.object_detections),
            selectinload(Asset.extraction_runs).selectinload(ExtractionRun.place_candidates),
        )
        .order_by(Asset.first_seen_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(session.scalars(q).all()), total


def list_folders(
    session: Session,
    *,
    folder_prefix: Optional[str] = None,
    media_type: Optional[str] = None,
    search: Optional[str] = None,
    ai_text: Optional[str] = None,
    scene: Optional[str] = None,
    place: Optional[str] = None,
    object_label: Optional[str] = None,
    has_ocr: Optional[bool] = None,
    has_gps: Optional[bool] = None,
    has_ai: Optional[bool] = None,
    review_bucket: Optional[str] = None,
) -> list[tuple[str, int]]:
    q = _apply_asset_filters(
        select(Asset),
        media_type=media_type,
        search=search,
        ai_text=ai_text,
        scene=scene,
        place=place,
        object_label=object_label,
        folder=folder_prefix,
        has_ocr=has_ocr,
        has_gps=has_gps,
        has_ai=has_ai,
        review_bucket=review_bucket,
    )

    assets = session.scalars(q.options(selectinload(Asset.temporal))).all()
    counts: dict[str, int] = {}
    normalized_prefix = (folder_prefix or "").strip("/")
    for asset in assets:
        root = Path(asset.source_root or "")
        try:
            relative_parent = str(Path(asset.canonical_path).relative_to(root).parent)
        except Exception:
            relative_parent = str(Path(asset.canonical_path).parent)
        if relative_parent in (".", ""):
            relative_parent = "/"
        relative_parent = relative_parent.replace("\\", "/")
        parts = [] if relative_parent == "/" else relative_parent.split("/")
        if normalized_prefix:
            prefix_parts = normalized_prefix.split("/")
            if parts[: len(prefix_parts)] != prefix_parts:
                continue
            next_parts = parts[: len(prefix_parts) + 1]
        else:
            next_parts = parts[:1]
        key = "/".join([part for part in next_parts if part]) or "/"
        counts[key] = counts.get(key, 0) + 1

    return sorted(counts.items(), key=lambda item: item[0])
