"""
Thumbnail & keyframe generation.

For images: resize to `max_width` (default 400px) using PIL.
For videos: extract 3 evenly-spaced keyframes via ffmpeg.
Both write to `{cache_root}/thumbs/{asset_id}/` and persist to DB.
"""
from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path

from PIL import Image
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).parents[2] / "db"))
from models import Asset, AssetThumbnail, Keyframe  # noqa: E402
from session import get_session  # noqa: E402

logger = logging.getLogger(__name__)

SUPPORTED_IMAGE_EXT = {
    ".jpg", ".jpeg", ".png", ".tiff", ".tif", ".heic", ".heif",
    ".webp", ".bmp", ".gif", ".avif", ".raw", ".cr2", ".cr3",
    ".nef", ".arw", ".orf", ".rw2", ".dng",
}
SUPPORTED_VIDEO_EXT = {
    ".mp4", ".mov", ".avi", ".mkv", ".mts", ".m2ts", ".m4v",
    ".wmv", ".flv", ".webm", ".3gp",
}


def _thumb_dir(cache_root: Path, asset_id: str) -> Path:
    d = cache_root / "thumbs" / asset_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def generate_image_thumbnail(
    session: Session,
    asset: Asset,
    cache_root: str,
    max_width: int = 400,
) -> AssetThumbnail | None:
    path = Path(asset.canonical_path)
    if not path.exists():
        logger.warning("Missing file: %s", path)
        return None

    out_dir = _thumb_dir(Path(cache_root), asset.id)
    out_path = out_dir / f"thumb_{max_width}.jpg"

    try:
        with Image.open(path) as img:
            img = img.convert("RGB")
            w, h = img.size
            if w > max_width:
                ratio = max_width / w
                img = img.resize((max_width, int(h * ratio)), Image.LANCZOS)
            new_w, new_h = img.size
            img.save(out_path, "JPEG", quality=85, optimize=True)
    except Exception:
        logger.exception("Thumbnail generation failed for %s", path)
        return None

    existing = session.query(AssetThumbnail).filter_by(
        asset_id=asset.id, width=new_w
    ).first()
    if existing:
        existing.path = str(out_path)
        existing.height = new_h
        return existing

    thumb = AssetThumbnail(
        asset_id=asset.id,
        path=str(out_path),
        width=new_w,
        height=new_h,
    )
    session.add(thumb)
    return thumb


def generate_video_keyframes(
    session: Session,
    asset: Asset,
    cache_root: str,
    num_frames: int = 3,
) -> list[Keyframe]:
    path = Path(asset.canonical_path)
    if not path.exists():
        return []

    # Get duration with ffprobe
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "quiet", "-print_format", "json",
                "-show_entries", "format=duration",
                str(path),
            ],
            capture_output=True, text=True, timeout=30,
        )
        import json
        probe = json.loads(result.stdout)
        duration = float(probe.get("format", {}).get("duration", 0))
    except Exception:
        logger.exception("ffprobe duration failed for %s", path)
        return []

    if duration <= 0:
        return []

    out_dir = _thumb_dir(Path(cache_root), asset.id)
    frames: list[Keyframe] = []

    for i in range(num_frames):
        offset = duration * (i + 1) / (num_frames + 1)
        out_path = out_dir / f"keyframe_{i:02d}.jpg"

        try:
            subprocess.run(
                [
                    "ffmpeg", "-y", "-ss", str(offset),
                    "-i", str(path),
                    "-vframes", "1",
                    "-vf", "scale=400:-2",
                    "-q:v", "5",
                    str(out_path),
                ],
                capture_output=True, timeout=30, check=True,
            )
        except Exception:
            logger.warning("Keyframe extraction failed at %.1fs for %s", offset, path)
            continue

        existing = session.query(Keyframe).filter_by(
            asset_id=asset.id, sequence_index=i
        ).first()
        if existing:
            existing.path = str(out_path)
            existing.offset_seconds = offset
            frames.append(existing)
        else:
            kf = Keyframe(
                asset_id=asset.id,
                path=str(out_path),
                offset_seconds=offset,
                sequence_index=i,
            )
            session.add(kf)
            frames.append(kf)

    return frames


def generate_thumbnails_for_asset(
    session: Session,
    asset: Asset,
    cache_root: str,
) -> None:
    ext = Path(asset.canonical_path).suffix.lower()
    if ext in SUPPORTED_IMAGE_EXT:
        generate_image_thumbnail(session, asset, cache_root, max_width=400)
        generate_image_thumbnail(session, asset, cache_root, max_width=1200)
    elif ext in SUPPORTED_VIDEO_EXT:
        generate_video_keyframes(session, asset, cache_root)


def generate_all_pending(cache_root: str) -> dict[str, int]:
    """Generate thumbnails for all assets that don't have them yet."""
    stats = {"processed": 0, "failed": 0, "skipped": 0}

    with get_session() as session:
        assets = session.query(Asset).filter_by(is_missing=False).all()
        for asset in assets:
            # Skip only if it already has BOTH sizes
            widths = {t.width for t in asset.thumbnails}
            if 400 in widths and 1200 in widths:
                stats["skipped"] += 1
                continue
            if asset.keyframes:
                stats["skipped"] += 1
                continue
            try:
                generate_thumbnails_for_asset(session, asset, cache_root)
                stats["processed"] += 1
            except Exception:
                logger.exception("Thumbnail job failed for asset %s", asset.id)
                stats["failed"] += 1

    return stats
