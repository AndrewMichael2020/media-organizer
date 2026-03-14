"""
ExifTool adapter — wraps the exiftool CLI.
Returns raw JSON payload and a normalized typed output.
Requires: brew install exiftool
"""
from __future__ import annotations

import json
import logging
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

EXIFTOOL_CMD = "exiftool"


@dataclass
class ExifData:
    raw: dict
    make: str | None = None
    model: str | None = None
    width: int | None = None
    height: int | None = None
    # Timestamps
    datetime_original: datetime | None = None
    datetime_digitized: datetime | None = None
    gps_latitude: float | None = None
    gps_longitude: float | None = None
    gps_altitude: float | None = None
    gps_datetime: datetime | None = None


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    for fmt in ("%Y:%m:%d %H:%M:%S", "%Y:%m:%d %H:%M:%S%z", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            return datetime.strptime(value[:19], fmt[:len(value[:19])])
        except ValueError:
            continue
    return None


def _parse_gps(value) -> float | None:
    """Convert ExifTool GPS coordinate to decimal degrees."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    # "48 deg 51' 24.00\" N" style — exiftool -n gives plain float
    try:
        return float(str(value).split()[0])
    except (ValueError, IndexError):
        return None


def extract_exif(path: Path) -> ExifData:
    """Run exiftool on a single file and return normalized ExifData."""
    try:
        out = subprocess.check_output(
            [EXIFTOOL_CMD, "-json", "-n", "-all:all", str(path)],
            stderr=subprocess.DEVNULL,
            timeout=30,
        )
        raw = json.loads(out)[0]
    except FileNotFoundError:
        raise RuntimeError("exiftool not found — run: brew install exiftool")
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"exiftool timed out on {path}")
    except Exception as exc:
        logger.warning("exiftool failed on %s: %s", path, exc)
        return ExifData(raw={})

    return ExifData(
        raw=raw,
        make=raw.get("Make"),
        model=raw.get("Model"),
        width=raw.get("ImageWidth") or raw.get("ExifImageWidth"),
        height=raw.get("ImageHeight") or raw.get("ExifImageHeight"),
        datetime_original=_parse_dt(raw.get("DateTimeOriginal")),
        datetime_digitized=_parse_dt(raw.get("CreateDate")),
        gps_latitude=_parse_gps(raw.get("GPSLatitude")),
        gps_longitude=_parse_gps(raw.get("GPSLongitude")),
        gps_altitude=_parse_gps(raw.get("GPSAltitude")),
        gps_datetime=_parse_dt(raw.get("GPSDateTime")),
    )
