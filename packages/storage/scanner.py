"""
Local filesystem scanner.
Recursively walks source roots, registers supported media assets in the catalog.
"""
from __future__ import annotations

import logging
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Allow importing packages/db
sys.path.insert(0, str(Path(__file__).parents[2] / "db"))

from session import get_session  # noqa: E402
from repositories.assets import (  # noqa: E402
    SUPPORTED_PHOTO_EXTS,
    SUPPORTED_VIDEO_EXTS,
    get_media_type,
    mark_missing,
    upsert_asset,
)

logger = logging.getLogger(__name__)


@dataclass
class ScanResult:
    source_root: str
    found: int = 0
    new: int = 0
    updated: int = 0
    skipped: int = 0
    marked_missing: int = 0
    errors: list[str] = field(default_factory=list)


def scan_source_root(source_root: str) -> ScanResult:
    """
    Walk source_root recursively, register all supported media assets.
    Idempotent — safe to rerun; only records delta changes.
    """
    root = Path(source_root).expanduser().resolve()
    result = ScanResult(source_root=str(root))

    if not root.exists():
        result.errors.append(f"Source root does not exist: {root}")
        logger.error(result.errors[-1])
        return result

    seen_paths: set[str] = set()

    with get_session() as session:
        for dirpath, _dirs, filenames in os.walk(root):
            for filename in filenames:
                if filename.startswith("."):
                    continue

                file_path = Path(dirpath) / filename
                canonical = str(file_path.resolve())
                media_type = get_media_type(file_path)

                if not media_type:
                    result.skipped += 1
                    continue

                result.found += 1
                seen_paths.add(canonical)

                try:
                    existing_id = _check_exists(session, canonical)
                    asset = upsert_asset(session, canonical, str(root))
                    if existing_id:
                        result.updated += 1
                    else:
                        result.new += 1
                        logger.debug("New asset: %s", canonical)
                except Exception as exc:
                    result.errors.append(f"{canonical}: {exc}")
                    logger.warning("Failed to register %s: %s", canonical, exc)

        result.marked_missing = mark_missing(session, str(root), seen_paths)

    logger.info(
        "Scan complete — root=%s found=%d new=%d updated=%d missing=%d errors=%d",
        root,
        result.found,
        result.new,
        result.updated,
        result.marked_missing,
        len(result.errors),
    )
    return result


def _check_exists(session, canonical_path: str) -> bool:
    from sqlalchemy import select
    from models import Asset
    return session.scalar(select(Asset.id).where(Asset.canonical_path == canonical_path)) is not None
