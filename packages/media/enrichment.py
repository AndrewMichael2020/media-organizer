"""
Deterministic enrichment — runs ExifTool + ffprobe on an asset
and persists normalized results to asset_media_info, asset_temporal,
and asset_location tables.
"""
from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).parents[2] / "db"))
from models import Asset, AssetLocation, AssetMediaInfo, AssetTemporal  # noqa: E402
from session import get_session  # noqa: E402

from exiftool import extract_exif  # noqa: E402
from ffprobe import extract_ffprobe  # noqa: E402

logger = logging.getLogger(__name__)


def enrich_asset(session: Session, asset: Asset) -> None:
    """Run deterministic enrichment for one asset. Idempotent — overwrites existing rows."""
    path = Path(asset.canonical_path)
    if not path.exists():
        logger.warning("Asset missing on disk: %s", path)
        return

    exif = extract_exif(path)

    if asset.media_type == "video":
        ffprobe = extract_ffprobe(path)
    else:
        ffprobe = None

    _persist_media_info(session, asset, exif, ffprobe)
    _persist_temporal(session, asset, exif, ffprobe)
    _persist_location(session, asset, exif)


def _persist_media_info(session, asset, exif, ffprobe):
    info = session.get(AssetMediaInfo, asset.id) if hasattr(asset, "id") else None
    # Look up by asset_id instead
    from sqlalchemy import select
    info = session.scalar(select(AssetMediaInfo).where(AssetMediaInfo.asset_id == asset.id))

    width = exif.width or (ffprobe.width if ffprobe else None)
    height = exif.height or (ffprobe.height if ffprobe else None)

    if info:
        info.width = width
        info.height = height
        info.make = exif.make
        info.model = exif.model
        info.exiftool_raw = exif.raw or {}
        if ffprobe:
            info.duration_seconds = ffprobe.duration_seconds
            info.video_codec = ffprobe.video_codec
            info.audio_codec = ffprobe.audio_codec
            info.frame_rate = ffprobe.frame_rate
            info.ffprobe_raw = ffprobe.raw or {}
        info.extracted_at = datetime.now(timezone.utc)
    else:
        info = AssetMediaInfo(
            asset_id=asset.id,
            width=width,
            height=height,
            make=exif.make,
            model=exif.model,
            exiftool_raw=exif.raw or {},
            duration_seconds=ffprobe.duration_seconds if ffprobe else None,
            video_codec=ffprobe.video_codec if ffprobe else None,
            audio_codec=ffprobe.audio_codec if ffprobe else None,
            frame_rate=ffprobe.frame_rate if ffprobe else None,
            ffprobe_raw=ffprobe.raw if ffprobe else None,
        )
        session.add(info)


def _persist_temporal(session, asset, exif, ffprobe):
    from sqlalchemy import select
    temporal = session.scalar(select(AssetTemporal).where(AssetTemporal.asset_id == asset.id))

    path = Path(asset.canonical_path)
    fs_mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)

    candidates = [
        ("exif", exif.datetime_original),
        ("exif", exif.datetime_digitized),
        ("gps", exif.gps_datetime),
        ("filesystem", fs_mtime),
    ]
    if ffprobe and ffprobe.creation_time:
        from datetime import timezone as tz_module
        try:
            dt = datetime.fromisoformat(ffprobe.creation_time.replace("Z", "+00:00"))
            candidates.append(("video", dt))
        except ValueError:
            pass

    best_ts, best_source, confidence = _resolve_best_timestamp(candidates)
    has_conflict = _has_conflict(candidates)

    if temporal:
        temporal.best_timestamp = best_ts
        temporal.best_timestamp_source = best_source
        temporal.best_timestamp_confidence = confidence
        temporal.exif_datetime = exif.datetime_original
        temporal.gps_datetime = exif.gps_datetime
        temporal.filesystem_mtime = fs_mtime
        temporal.has_conflict = has_conflict
    else:
        temporal = AssetTemporal(
            asset_id=asset.id,
            best_timestamp=best_ts,
            best_timestamp_source=best_source,
            best_timestamp_confidence=confidence,
            exif_datetime=exif.datetime_original,
            gps_datetime=exif.gps_datetime,
            filesystem_mtime=fs_mtime,
            has_conflict=has_conflict,
        )
        session.add(temporal)


def _resolve_best_timestamp(candidates):
    """Pick the most trustworthy timestamp. Priority: gps > exif > video > filesystem."""
    priority = {"gps": 0, "exif": 1, "video": 2, "filesystem": 3}
    valid = [(src, dt) for src, dt in candidates if dt is not None]
    if not valid:
        return None, None, "low"
    valid.sort(key=lambda x: priority.get(x[0], 99))
    src, dt = valid[0]
    confidence = "high" if src in ("gps", "exif") else "medium" if src == "video" else "low"
    return dt, src, confidence


def _has_conflict(candidates) -> bool:
    """True if exif and gps timestamps differ by more than 1 day."""
    times = {src: dt for src, dt in candidates if dt is not None and src in ("exif", "gps")}
    if "exif" in times and "gps" in times:
        delta = abs((times["exif"] - times["gps"]).total_seconds())
        return delta > 86400
    return False


def _persist_location(session, asset, exif):
    if exif.gps_latitude is None or exif.gps_longitude is None:
        return
    from sqlalchemy import select
    location = session.scalar(select(AssetLocation).where(AssetLocation.asset_id == asset.id))
    if location:
        location.latitude = exif.gps_latitude
        location.longitude = exif.gps_longitude
        location.altitude_m = exif.gps_altitude
        location.gps_source = "exif"
        location.location_raw = {
            "latitude": exif.gps_latitude,
            "longitude": exif.gps_longitude,
        }
    else:
        session.add(AssetLocation(
            asset_id=asset.id,
            latitude=exif.gps_latitude,
            longitude=exif.gps_longitude,
            altitude_m=exif.gps_altitude,
            gps_source="exif",
            location_raw={"latitude": exif.gps_latitude, "longitude": exif.gps_longitude},
        ))


def enrich_all_pending(
    limit: int = 200,
    folder_path: str | None = None,
    should_cancel: Callable[[], bool] | None = None,
) -> tuple[int, int, bool]:
    """Enrich assets that don't yet have media_info. Returns (done, errors)."""
    done = errors = 0
    cancelled = False
    with get_session() as session:
        from sqlalchemy import select
        from models import Asset, AssetMediaInfo
        enriched_ids = select(AssetMediaInfo.asset_id)
        q = select(Asset).where(Asset.id.not_in(enriched_ids), Asset.is_missing == False)  # noqa: E712
        if folder_path:
            q = q.where((Asset.canonical_path == folder_path) | (Asset.canonical_path.like(f"{folder_path}/%")))
        assets = session.scalars(q.limit(limit)).all()
        for asset in assets:
            if should_cancel and should_cancel():
                cancelled = True
                break
            try:
                enrich_asset(session, asset)
                done += 1
            except Exception as exc:
                logger.warning("Enrich failed %s: %s", asset.canonical_path, exc)
                errors += 1
    return done, errors, cancelled
