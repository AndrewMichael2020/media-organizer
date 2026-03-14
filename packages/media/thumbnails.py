"""
Thumbnail & keyframe generation.

Standard images are resized with PIL.
RAW files prefer the camera-embedded preview via ExifTool because it is
usually much sharper and faster than decoding RAW data directly with PIL.
"""
from __future__ import annotations

import logging
import platform
import subprocess
import sys
from io import BytesIO
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Callable

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
RAW_IMAGE_EXT = {".raw", ".cr2", ".cr3", ".nef", ".arw", ".orf", ".rw2", ".dng"}
APPLE_IMAGE_EXT = {".heic", ".heif"}
SUPPORTED_VIDEO_EXT = {
    ".mp4", ".mov", ".avi", ".mkv", ".mts", ".m2ts", ".m4v",
    ".wmv", ".flv", ".webm", ".3gp",
}
THUMB_SIZES = (640, 1600)


def _thumb_dir(cache_root: Path, asset_id: str) -> Path:
    d = cache_root / "thumbs" / asset_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def _open_best_image(asset: Asset) -> Image.Image:
    path = Path(asset.canonical_path)
    ext = path.suffix.lower()

    if ext in RAW_IMAGE_EXT:
        for preview_tag in ("PreviewImage", "JpgFromRaw", "OtherImage"):
            try:
                preview = subprocess.run(
                    ["exiftool", f"-b", f"-{preview_tag}", str(path)],
                    capture_output=True,
                    timeout=30,
                    check=False,
                )
            except Exception:
                if preview.returncode == 0 and preview.stdout:
                    return Image.open(BytesIO(preview.stdout)).copy()
            except Exception:
                logger.warning("Embedded RAW preview decode failed for %s via %s", path.name, preview_tag)

    if ext in APPLE_IMAGE_EXT and platform.system() == "Darwin":
        try:
            with NamedTemporaryFile(suffix=".jpg") as tmp:
                subprocess.run(
                    ["sips", "-s", "format", "jpeg", str(path), "--out", tmp.name],
                    capture_output=True,
                    timeout=45,
                    check=True,
                )
                with Image.open(tmp.name) as img:
                    return img.copy()
        except Exception:
            logger.warning("sips conversion failed for %s", path.name)

    with Image.open(path) as img:
        return img.copy()


def _save_resized_jpeg(image: Image.Image, out_path: Path, max_width: int) -> tuple[int, int]:
    img = image.convert("RGB")
    w, h = img.size
    if w > max_width:
        ratio = max_width / w
        img = img.resize((max_width, max(1, int(h * ratio))), Image.LANCZOS)
    new_w, new_h = img.size
    img.save(out_path, "JPEG", quality=90, optimize=True, progressive=True)
    return new_w, new_h


def generate_image_thumbnail(
    session: Session,
    asset: Asset,
    cache_root: str,
    max_width: int = 640,
) -> AssetThumbnail | None:
    path = Path(asset.canonical_path)
    if not path.exists():
        logger.warning("Missing file: %s", path)
        return None

    out_dir = _thumb_dir(Path(cache_root), asset.id)
    out_path = out_dir / f"thumb_{max_width}.jpg"

    try:
        image = _open_best_image(asset)
        try:
            new_w, new_h = _save_resized_jpeg(image, out_path, max_width=max_width)
        finally:
            image.close()
    except Exception:
        logger.exception("Thumbnail generation failed for %s", path)
        return None

    existing = session.query(AssetThumbnail).filter_by(asset_id=asset.id, width=new_w).first()
    if existing:
        existing.path = str(out_path)
        existing.height = new_h
        return existing

    thumb = AssetThumbnail(asset_id=asset.id, path=str(out_path), width=new_w, height=new_h)
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
                    "-vf", "scale=960:-2",
                    "-q:v", "3",
                    str(out_path),
                ],
                capture_output=True, timeout=30, check=True,
            )
        except Exception:
            logger.warning("Keyframe extraction failed at %.1fs for %s", offset, path)
            continue

        existing = session.query(Keyframe).filter_by(asset_id=asset.id, sequence_index=i).first()
        if existing:
            existing.path = str(out_path)
            existing.offset_seconds = offset
            frames.append(existing)
        else:
            kf = Keyframe(asset_id=asset.id, path=str(out_path), offset_seconds=offset, sequence_index=i)
            session.add(kf)
            frames.append(kf)

    return frames


def generate_thumbnails_for_asset(session: Session, asset: Asset, cache_root: str) -> None:
    ext = Path(asset.canonical_path).suffix.lower()
    if ext in SUPPORTED_IMAGE_EXT:
        for size in THUMB_SIZES:
            generate_image_thumbnail(session, asset, cache_root, max_width=size)
    elif ext in SUPPORTED_VIDEO_EXT:
        generate_video_keyframes(session, asset, cache_root)


def generate_all_pending(
    cache_root: str,
    folder_path: str | None = None,
    should_cancel: Callable[[], bool] | None = None,
) -> dict[str, int | bool]:
    """Generate thumbnails for all assets that don't have the preferred sizes yet."""
    stats = {"processed": 0, "failed": 0, "skipped": 0, "cancelled": False}

    with get_session() as session:
        q = session.query(Asset).filter_by(is_missing=False)
        if folder_path:
            q = q.filter((Asset.canonical_path == folder_path) | (Asset.canonical_path.like(f"{folder_path}/%")))
        assets = q.all()
        for asset in assets:
            if should_cancel and should_cancel():
                stats["cancelled"] = True
                break
            widths = {t.width for t in asset.thumbnails}
            if set(THUMB_SIZES).issubset(widths):
                stats["skipped"] += 1
                continue
            if asset.media_type == "video" and asset.keyframes:
                stats["skipped"] += 1
                continue
            try:
                generate_thumbnails_for_asset(session, asset, cache_root)
                stats["processed"] += 1
            except Exception:
                logger.exception("Thumbnail job failed for asset %s", asset.id)
                stats["failed"] += 1

    return stats
