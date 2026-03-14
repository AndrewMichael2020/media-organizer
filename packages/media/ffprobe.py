"""
ffprobe adapter — wraps ffprobe CLI for video metadata.
Requires: brew install ffmpeg
"""
from __future__ import annotations

import json
import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class FfprobeData:
    raw: dict
    width: int | None = None
    height: int | None = None
    duration_seconds: float | None = None
    video_codec: str | None = None
    audio_codec: str | None = None
    frame_rate: float | None = None
    creation_time: str | None = None


def extract_ffprobe(path: Path) -> FfprobeData:
    """Run ffprobe on a file and return normalized FfprobeData."""
    try:
        out = subprocess.check_output(
            [
                "ffprobe", "-v", "quiet",
                "-print_format", "json",
                "-show_format", "-show_streams",
                str(path),
            ],
            stderr=subprocess.DEVNULL,
            timeout=60,
        )
        raw = json.loads(out)
    except FileNotFoundError:
        raise RuntimeError("ffprobe not found — run: brew install ffmpeg")
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"ffprobe timed out on {path}")
    except Exception as exc:
        logger.warning("ffprobe failed on %s: %s", path, exc)
        return FfprobeData(raw={})

    streams = raw.get("streams", [])
    fmt = raw.get("format", {})

    video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)

    frame_rate = None
    if video_stream:
        r_frame_rate = video_stream.get("r_frame_rate", "")
        try:
            num, den = r_frame_rate.split("/")
            frame_rate = round(int(num) / int(den), 3) if int(den) else None
        except (ValueError, ZeroDivisionError):
            pass

    return FfprobeData(
        raw=raw,
        width=video_stream.get("width") if video_stream else None,
        height=video_stream.get("height") if video_stream else None,
        duration_seconds=float(fmt["duration"]) if fmt.get("duration") else None,
        video_codec=video_stream.get("codec_name") if video_stream else None,
        audio_codec=audio_stream.get("codec_name") if audio_stream else None,
        frame_rate=frame_rate,
        creation_time=fmt.get("tags", {}).get("creation_time"),
    )
