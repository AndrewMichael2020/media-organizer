"""
Asset repository — CRUD operations for the asset catalog.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.orm import Session

# Add db package to path for sibling import
import sys
sys.path.insert(0, str(Path(__file__).parents[2] / "db"))

from models import Asset, AssetHash  # noqa: E402


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


def list_assets(
    session: Session,
    *,
    media_type: Optional[str] = None,
    search: Optional[str] = None,
    has_thumbnail: Optional[bool] = None,
    page: int = 1,
    page_size: int = 48,
) -> tuple[list[Asset], int]:
    from sqlalchemy import or_, func, text

    q = select(Asset).where(Asset.is_missing == False)  # noqa: E712
    if media_type:
        q = q.where(Asset.media_type == media_type)

    if search and search.strip():
        term = search.strip()
        # Simple ILIKE on filename and canonical_path — works without FTS index
        pattern = f"%{term}%"
        q = q.where(
            or_(
                Asset.filename.ilike(pattern),
                Asset.canonical_path.ilike(pattern),
            )
        )

    # Count before pagination
    from sqlalchemy import func as sa_func
    count_q = select(sa_func.count()).select_from(q.subquery())
    total = session.scalar(count_q) or 0

    q = q.order_by(Asset.first_seen_at.desc()).offset((page - 1) * page_size).limit(page_size)
    return list(session.scalars(q).all()), total
