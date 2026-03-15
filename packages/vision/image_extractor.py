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
    SceneSummary as DBSceneSummary, PlaceCandidate as DBPlaceCandidate, Assertion,
)
from session import get_session  # noqa: E402
from sqlalchemy import delete as sa_delete  # noqa: E402

# Model router + schemas (same package dir pattern as other packages)
sys.path.insert(0, str(Path(__file__).parents[2] / "models"))
from router import get_provider  # noqa: E402
from provider import ModelProvider  # noqa: E402
from schemas import ImageExtractionOutput, SCHEMA_VERSION  # noqa: E402

logger = logging.getLogger(__name__)

_PRICING_PER_M_TOKENS: dict[tuple[str, str], tuple[float, float]] = {
    ("gemini-2.5-flash-lite", "standard"): (0.10, 0.40),
    ("gemini-2.5-flash-lite", "batch"): (0.05, 0.20),
    ("gemini-3.1-flash-lite-preview", "standard"): (0.25, 1.50),
    ("gemini-3.1-flash-lite-preview", "batch"): (0.125, 0.75),
}


def _calculate_cost(tokens_in: int, tokens_out: int, model_name: str, execution_mode: str = "standard") -> float:
    rates = _PRICING_PER_M_TOKENS.get((model_name, execution_mode))
    if rates is None:
        base = _PRICING_PER_M_TOKENS.get((model_name, "standard"))
        if base is None:
            base = _PRICING_PER_M_TOKENS[("gemini-3.1-flash-lite-preview", "standard")]
        rates = (base[0] * 0.5, base[1] * 0.5) if execution_mode == "batch" else base
    return (tokens_in * rates[0] + tokens_out * rates[1]) / 1_000_000


def _user_context_prompt(session: Session, asset_id: str) -> str:
    from sqlalchemy import select as sa_select

    rows = session.scalars(
        sa_select(Assertion)
        .where(
            Assertion.asset_id == asset_id,
            Assertion.is_active == True,  # noqa: E712
            Assertion.predicate.in_(["user.place", "user.gps_coords", "user.comments"]),
        )
        .order_by(Assertion.created_at.desc())
    ).all()

    values: dict[str, str | None] = {"place": None, "gps_coords": None, "comments": None}
    for row in rows:
        key = row.predicate.replace("user.", "", 1)
        if key in values and not values[key]:
            cleaned = str(row.value or "").strip()
            values[key] = cleaned or None

    lines: list[str] = []
    if values["place"]:
        lines.append(f"- User place note: {values['place']}")
    if values["gps_coords"]:
        lines.append(f"- User GPS coordinates: {values['gps_coords']}")
    if values["comments"]:
        lines.append(f"- User comments: {values['comments']}")
    if not lines:
        return ""
    return (
        "\n\nUser-supplied archival context:\n"
        + "\n".join(lines)
        + "\nUse this context as optional input for place and scene interpretation. "
          "Treat it as user-provided context, not as visual proof, and do not repeat unsupported claims."
    )


def _ocr_context_prompt(session: Session, asset_id: str) -> str:
    from sqlalchemy import select as sa_select

    ocr_doc = session.scalar(
        sa_select(OcrDocument)
        .join(ExtractionRun, ExtractionRun.id == OcrDocument.extraction_run_id)
        .where(
            ExtractionRun.asset_id == asset_id,
            ExtractionRun.status == "done",
        )
        .order_by(ExtractionRun.started_at.desc())
    )
    if not ocr_doc or not ocr_doc.full_text:
        return ""
    text = re.sub(r"\s+", " ", ocr_doc.full_text).strip()
    if not text:
        return ""
    return (
        "\n\nOCR context from a previous archival pass:\n"
        f"- Visible text candidate: {text[:700]}\n"
        "Use this only as OCR input context. Prefer it when it clarifies signage, institutions, site names, "
        "uniform text, or building text that is actually visible. Do not expand it beyond what the OCR supports."
    )

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
HYPER_OPTIMIZED_MAX_PX = 768
MAX_ORIGINAL_BYTES = 8 * 1024 * 1024  # 8 MB — above this, prefer the thumbnail
ANALYSIS_THUMB_WIDTH = 1200  # preferred thumbnail size for AI analysis
DEFAULT_MAX_OUTPUT_TOKENS = None
DEFAULT_JPEG_QUALITY = 85
HYPER_OPTIMIZED_JPEG_QUALITY = 60
AI_DEBUG_DIR = Path(__file__).parents[2] / "var" / "ai_debug"

_CONFIDENCE_MAP = {"low": "low", "medium": "medium", "med": "medium", "high": "high", "unknown": "unknown"}
_ROLE_MAP = {
    "marine_biologist": "research_or_fieldwork_personnel",
    "combat_medic": "emergency_responder",
    "alpine_guide": "coach_or_instructor",
    "infantry_sergeant": "security_personnel",
    "undercover_officer": "plainclothes_security_possible",
}

_ALLOWED_PRIMARY_SCENES = {
    "urban_street", "beach", "waterfront_nonbeach", "park", "residential", "industrial_site", "healthcare",
    "laboratory", "classroom", "conference", "office", "transit_area", "crowd_event", "checkpoint_or_security_area",
    "damaged_built_environment", "active_conflict_or_aftermath", "emergency_response_scene", "mountain_landscape",
    "alpine_climbing_scene", "rock_climbing_scene", "glacier_or_snowfield", "trail_or_backcountry", "other",
}
_ALLOWED_IMAGE_TYPE = {"candid_photo", "posed_photo", "screenshot", "surveillance_like", "scanned_document_photo", "press_photo_like", "promotional_photo_like", "unknown"}
_ALLOWED_ENVIRONMENT = {"public", "semi_public", "private", "institutional", "commercial", "natural", "unknown"}
_ALLOWED_INDOOR = {"indoor", "outdoor", "mixed", "unknown"}
_ALLOWED_CROWD = {"none", "sparse", "moderate", "dense"}
_ALLOWED_GROUP = {"alone", "pair", "small_group", "large_group", "crowd", "unknown"}
_ALLOWED_ACTIVITY = {"walking", "waiting", "observing", "presentation", "leisure", "transit", "clinical_work", "lab_work", "security_activity", "emergency_response", "crowd_gathering", "climbing", "belaying", "scrambling", "mountaineering", "skiing_or_snow_travel", "unknown"}
_ALLOWED_VISIBILITY = {"full_body", "upper_body", "partial_body", "face_only", "back_view", "occluded", "unknown"}
_ALLOWED_AGE = {"child", "teen", "adult", "older_adult", "unknown"}
_ALLOWED_POSTURE = {"standing", "sitting", "walking_posture", "crouching", "climbing_posture", "belaying_posture", "kneeling", "lying", "unknown"}
_ALLOWED_TEXT_CONTEXT = {"signage", "badge", "uniform_text", "vehicle_marking", "placard", "storefront", "whiteboard", "document_fragment", "building_marking", "checkpoint_marking", "trail_sign", "route_marker", "equipment_label"}
_ALLOWED_PUBLIC_PRIVATE = {"public", "semi_public", "private", "unknown", "natural"}
_ALLOWED_ICL = {"institutional", "commercial", "leisure", "civic", "residential", "natural", "unknown"}
_ALLOWED_ECON = {"luxury", "middle_class", "working_class_or_utilitarian", "impoverished_or_deprived", "mixed", "not_applicable", "unknown"}
_ALLOWED_TECH = {"low", "medium", "high", "unknown"}
_ALLOWED_LOCATION_SOURCE = {"embedded_metadata", "ocr_text", "landmark_visual_inference", "combined", "unknown"}
_ALLOWED_LOCATION_PRECISION = {"exact_place", "site_level", "city_level", "province_or_state_level", "country_level", "place_type_only", "unknown"}
_ALLOWED_SECURITY = {"none_visible", "low", "medium", "high", "unknown"}
_ALLOWED_MOBILITY = {"pedestrian_flow", "vehicle_flow", "blocked_route", "controlled_access", "staging_area", "evacuation_like", "vertical_progression", "rope_protected_movement", "unknown"}
_ALLOWED_INFRA = {"normal", "damaged", "heavily_damaged", "temporary_barriers_present", "smoke_or_fire_present", "utility_disruption_possible", "natural_terrain", "unknown"}
_ALLOWED_TERRAIN = {"flat_urban", "beach", "forest", "trail", "talus_or_scree", "rock_wall", "alpine_ridge", "glacier", "snowfield", "mixed_mountain_terrain", "desert_or_barren", "water_edge", "unknown"}
_ALLOWED_SLOPE = {"flat", "gentle", "steep", "very_steep", "vertical_or_near_vertical", "unknown"}
_ALLOWED_SNOW = {"none_visible", "patchy_snow", "continuous_snow", "glacier_ice_possible", "mixed_snow_rock", "unknown"}
_ALLOWED_WATER = {"none_visible", "lake", "river", "waterfall", "surf_or_ocean", "shoreline", "glacial_stream", "unknown"}
_ALLOWED_VEG = {"urban", "beach_margin", "forested", "subalpine", "alpine", "barren_high_alpine", "unknown"}
_ALLOWED_EXPOSURE = {"low", "moderate", "high", "extreme", "unknown"}
_ALLOWED_WEATHER_VIS = {"clear", "overcast", "fog_or_cloud_obscuration", "blowing_snow_possible", "stormy_possible", "smoke_haze_possible", "unknown"}
_ALLOWED_SEVERITY = {"low", "medium", "high"}
_ALLOWED_FRAMING = {"close_up", "medium_shot", "wide_shot", "cropped_subject", "obstructed_view", "unknown"}


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


def _pil_to_jpeg_bytes(path: Path, max_px: int = MAX_GEMINI_PX, jpeg_quality: int = DEFAULT_JPEG_QUALITY) -> bytes:
    """Open a PIL-readable image, downscale if needed, return JPEG bytes."""
    with Image.open(path) as img:
        img = img.convert("RGB")
        w, h = img.size
        if max(w, h) > max_px:
            ratio = max_px / max(w, h)
            img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)
        buf = BytesIO()
        img.save(buf, "JPEG", quality=jpeg_quality)
        return buf.getvalue()


def _apple_to_jpeg_bytes(path: Path, max_px: int = MAX_GEMINI_PX, jpeg_quality: int = DEFAULT_JPEG_QUALITY) -> bytes:
    with NamedTemporaryFile(suffix=".jpg") as tmp:
        subprocess = __import__("subprocess")
        subprocess.run(
            ["sips", "-Z", str(max_px), "-s", "format", "jpeg", str(path), "--out", tmp.name],
            capture_output=True,
            timeout=60,
            check=True,
        )
        if jpeg_quality >= DEFAULT_JPEG_QUALITY:
            return Path(tmp.name).read_bytes()
        with Image.open(tmp.name) as img:
            img = img.convert("RGB")
            buf = BytesIO()
            img.save(buf, "JPEG", quality=jpeg_quality)
            return buf.getvalue()


def _resolve_image_bytes(
    asset: Asset,
    path: Path,
    max_px: int = MAX_GEMINI_PX,
    jpeg_quality: int = DEFAULT_JPEG_QUALITY,
) -> tuple[bytes, str]:
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
            return _apple_to_jpeg_bytes(path, max_px=max_px, jpeg_quality=jpeg_quality), "image/jpeg"
        except Exception as exc:
            logger.warning("sips failed on %s (%s), falling back", path.name, exc)

    if not is_raw and not is_large:
        # Happy path: PIL-readable, reasonably sized
        try:
            return _pil_to_jpeg_bytes(path, max_px=max_px, jpeg_quality=jpeg_quality), "image/jpeg"
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
    return _pil_to_jpeg_bytes(path, max_px=max_px, jpeg_quality=jpeg_quality), "image/jpeg"


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


def _norm_text(value: str | None, max_len: int = 220) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = re.sub(r"\s+", " ", value).strip()
    return cleaned[:max_len] if cleaned else None


def _norm_enum(value: str | None, allowed: set[str], default: str = "unknown") -> str:
    if not isinstance(value, str):
        return default
    normalized = value.strip().lower().replace(" ", "_").replace("-", "_")
    return normalized if normalized in allowed else default


def _norm_confidence(value) -> str:
    if isinstance(value, (int, float)):
        if value >= 0.85:
            return "high"
        if value >= 0.55:
            return "medium"
        if value >= 0:
            return "low"
    if isinstance(value, str):
        normalized = value.strip().lower()
        return _CONFIDENCE_MAP.get(normalized, "unknown")
    return "unknown"


def _dedupe_strings(values, cap: int, allowed: set[str] | None = None) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for value in values or []:
        if not isinstance(value, str):
            continue
        cleaned = value.strip().lower().replace(" ", "_").replace("-", "_")
        if not cleaned:
            continue
        if allowed and cleaned not in allowed:
            continue
        if cleaned in seen:
            continue
        output.append(cleaned)
        seen.add(cleaned)
        if len(output) >= cap:
            break
    return output


def _normalize_hypotheses(items, cap: int) -> list[dict]:
    output: list[dict] = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        label = item.get("label")
        if not isinstance(label, str) or not label.strip():
            continue
        normalized_label = _ROLE_MAP.get(label.strip().lower().replace(" ", "_"), label.strip().lower().replace(" ", "_"))
        evidence = [_norm_text(entry, 60) for entry in item.get("evidence") or []]
        evidence = [entry for entry in evidence if entry][:5]
        if not evidence:
            continue
        output.append({
            "label": normalized_label,
            "confidence": _norm_confidence(item.get("confidence")),
            "evidence": evidence,
        })
        if len(output) >= cap:
            break
    return output


def _normalize_output(output: ImageExtractionOutput) -> ImageExtractionOutput:
    raw = output.model_dump()
    summary = raw["image_summary"]
    summary["strict_caption"] = _norm_text(summary.get("strict_caption"), 220)
    summary["primary_scene"] = _norm_enum(summary.get("primary_scene"), _ALLOWED_PRIMARY_SCENES, "other")
    summary["secondary_scenes"] = _dedupe_strings(summary.get("secondary_scenes"), 5)
    summary["indoor_outdoor"] = _norm_enum(summary.get("indoor_outdoor"), _ALLOWED_INDOOR)
    summary["environment_type"] = _norm_enum(summary.get("environment_type"), _ALLOWED_ENVIRONMENT)
    summary["image_type"] = _norm_enum(summary.get("image_type"), _ALLOWED_IMAGE_TYPE)
    summary["location_cues"] = [_norm_text(item, 60) for item in summary.get("location_cues") or []]
    summary["location_cues"] = [item for item in summary["location_cues"] if item][:5]
    summary["time_of_day"] = _norm_text(summary.get("time_of_day"), 40)
    summary["season_cues"] = _dedupe_strings(summary.get("season_cues"), 4)
    summary["historical_modernity_cues"] = [_norm_text(item, 50) for item in summary.get("historical_modernity_cues") or []]
    summary["historical_modernity_cues"] = [item for item in summary["historical_modernity_cues"] if item][:4]
    summary["confidence"] = _norm_confidence(summary.get("confidence"))

    people_overview = raw["people_overview"]
    people_overview["people_count_visible"] = max(0, int(people_overview.get("people_count_visible") or 0))
    people_overview["crowd_density"] = _norm_enum(people_overview.get("crowd_density"), _ALLOWED_CROWD, "none")
    people_overview["group_structure"] = _norm_enum(people_overview.get("group_structure"), _ALLOWED_GROUP)
    people_overview["dominant_activity"] = _norm_enum(people_overview.get("dominant_activity"), _ALLOWED_ACTIVITY)
    people_overview["confidence"] = _norm_confidence(people_overview.get("confidence"))

    normalized_people: list[dict] = []
    for person in raw.get("people") or []:
        if not isinstance(person, dict):
            continue
        normalized_people.append({
            "visibility": _norm_enum(person.get("visibility"), _ALLOWED_VISIBILITY),
            "apparent_age_band": _norm_enum(person.get("apparent_age_band"), _ALLOWED_AGE),
            "clothing_items": _dedupe_strings(person.get("clothing_items"), 8),
            "uniform_indicators": _dedupe_strings(person.get("uniform_indicators"), 5),
            "accessories": _dedupe_strings(person.get("accessories"), 5),
            "posture": _norm_enum(person.get("posture"), _ALLOWED_POSTURE),
            "actions": _dedupe_strings(person.get("actions"), 5),
            "visible_expression_cues": _dedupe_strings(person.get("visible_expression_cues"), 4),
            "carried_or_worn_gear": _dedupe_strings(person.get("carried_or_worn_gear"), 6),
            "visual_signature_cues": _dedupe_strings(person.get("visual_signature_cues"), 5),
            "role_hypotheses": _normalize_hypotheses(person.get("role_hypotheses"), 3),
            "confidence": _norm_confidence(person.get("confidence")),
        })
        if len(normalized_people) >= 8:
            break
    raw["people"] = normalized_people

    normalized_objects: list[dict] = []
    for obj in raw.get("objects") or []:
        if not isinstance(obj, dict):
            continue
        label = _norm_text(obj.get("object_label"), 60)
        if not label:
            continue
        normalized_objects.append({
            "object_label": label.lower().replace(" ", "_"),
            "count_estimate": max(1, int(obj.get("count_estimate") or 1)),
            "significance": _norm_enum(obj.get("significance"), {"high", "medium", "low"}, "low"),
            "evidence": [item for item in (_norm_text(entry, 60) for entry in obj.get("evidence") or []) if item][:5],
        })
        if len(normalized_objects) >= 12:
            break
    raw["objects"] = normalized_objects

    normalized_text_regions: list[dict] = []
    for region in raw.get("text_regions") or []:
        if not isinstance(region, dict):
            continue
        text = _norm_text(region.get("text"), 200)
        if not text:
            continue
        normalized_text_regions.append({
            "text": text,
            "context": _norm_enum(region.get("context"), _ALLOWED_TEXT_CONTEXT, "signage"),
            "confidence": _norm_confidence(region.get("confidence")),
        })
        if len(normalized_text_regions) >= 10:
            break
    raw["text_regions"] = normalized_text_regions

    setting = raw["setting_analysis"]
    setting["setting_type_hypotheses"] = _normalize_hypotheses(setting.get("setting_type_hypotheses"), 4)
    setting["place_type_hypotheses"] = _normalize_hypotheses(setting.get("place_type_hypotheses"), 4)
    setting["public_private"] = _norm_enum(setting.get("public_private"), _ALLOWED_PUBLIC_PRIVATE)
    setting["institutional_commercial_leisure"] = _norm_enum(setting.get("institutional_commercial_leisure"), _ALLOWED_ICL)
    setting["built_environment_economic_signal"] = _norm_enum(setting.get("built_environment_economic_signal"), _ALLOWED_ECON)
    setting["technical_signal"] = _norm_enum(setting.get("technical_signal"), _ALLOWED_TECH)
    setting["visible_logos"] = [_norm_text(item, 40) for item in setting.get("visible_logos") or []]
    setting["visible_logos"] = [item for item in setting["visible_logos"] if item][:5]
    setting["visible_insignia"] = [_norm_text(item, 40) for item in setting.get("visible_insignia") or []]
    setting["visible_insignia"] = [item for item in setting["visible_insignia"] if item][:5]
    setting["organization_text_cues"] = [_norm_text(item, 60) for item in setting.get("organization_text_cues") or []]
    setting["organization_text_cues"] = [item for item in setting["organization_text_cues"] if item][:5]
    setting["confidence"] = _norm_confidence(setting.get("confidence"))

    location_meta = raw["location_meta"]
    location_meta["place_name_candidate"] = _norm_text(location_meta.get("place_name_candidate"), 120)
    location_meta["nearest_city_candidate"] = _norm_text(location_meta.get("nearest_city_candidate"), 80)
    location_meta["province_or_state_candidate"] = _norm_text(location_meta.get("province_or_state_candidate"), 80)
    location_meta["country_candidate"] = _norm_text(location_meta.get("country_candidate"), 80)
    location_meta["location_source"] = _norm_enum(location_meta.get("location_source"), _ALLOWED_LOCATION_SOURCE)
    location_meta["location_precision"] = _norm_enum(location_meta.get("location_precision"), _ALLOWED_LOCATION_PRECISION)
    location_meta["location_confidence"] = _norm_confidence(location_meta.get("location_confidence"))
    location_meta["location_evidence"] = [item for item in (_norm_text(entry, 70) for entry in location_meta.get("location_evidence") or []) if item][:5]

    operational = raw["operational_context"]
    operational["scene_function_hypotheses"] = _normalize_hypotheses(operational.get("scene_function_hypotheses"), 4)
    operational["security_presence"] = _norm_enum(operational.get("security_presence"), _ALLOWED_SECURITY)
    operational["covert_or_plainclothes_indicators"] = _dedupe_strings(operational.get("covert_or_plainclothes_indicators"), 5)
    operational["damage_indicators"] = _dedupe_strings(operational.get("damage_indicators"), 5)
    operational["threat_indicators"] = _dedupe_strings(operational.get("threat_indicators"), 5)
    operational["mobility_context"] = _norm_enum(operational.get("mobility_context"), _ALLOWED_MOBILITY)
    operational["infrastructure_status"] = _norm_enum(operational.get("infrastructure_status"), _ALLOWED_INFRA)
    operational["confidence"] = _norm_confidence(operational.get("confidence"))

    landscape = raw["landscape_analysis"]
    landscape["terrain_type"] = _norm_enum(landscape.get("terrain_type"), _ALLOWED_TERRAIN)
    landscape["slope_character"] = _norm_enum(landscape.get("slope_character"), _ALLOWED_SLOPE)
    landscape["rock_type_visual_cues"] = _dedupe_strings(landscape.get("rock_type_visual_cues"), 4)
    landscape["snow_ice_presence"] = _norm_enum(landscape.get("snow_ice_presence"), _ALLOWED_SNOW)
    landscape["water_features"] = _norm_enum(landscape.get("water_features"), _ALLOWED_WATER)
    landscape["vegetation_zone"] = _norm_enum(landscape.get("vegetation_zone"), _ALLOWED_VEG)
    landscape["route_or_access_cues"] = _dedupe_strings(landscape.get("route_or_access_cues"), 5)
    landscape["exposure_level"] = _norm_enum(landscape.get("exposure_level"), _ALLOWED_EXPOSURE)
    landscape["weather_visibility_cues"] = _norm_enum(landscape.get("weather_visibility_cues"), _ALLOWED_WEATHER_VIS)
    landscape["confidence"] = _norm_confidence(landscape.get("confidence"))

    sensitivity = raw["sensitivity_review"]
    sensitivity["flags"] = _dedupe_strings(sensitivity.get("flags"), 8)
    if not sensitivity["flags"]:
        sensitivity["flags"] = ["none"]
    sensitivity["severity"] = _norm_enum(sensitivity.get("severity"), _ALLOWED_SEVERITY, "low")
    sensitivity["reasons"] = [item for item in (_norm_text(entry, 60) for entry in sensitivity.get("reasons") or []) if item][:5]

    quality = raw["quality_review"]
    quality["image_quality"] = _norm_text(quality.get("image_quality"), 80)
    quality["occlusion_level"] = _norm_text(quality.get("occlusion_level"), 60)
    quality["framing"] = _norm_enum(quality.get("framing"), _ALLOWED_FRAMING)
    quality["limitations"] = [item for item in (_norm_text(entry, 60) for entry in quality.get("limitations") or []) if item][:6]

    return ImageExtractionOutput.model_validate(raw)


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

    ocr_text = "\n".join(region.text for region in output.text_regions if region.text).strip()
    overall_confidence = {
        "high": 0.92,
        "medium": 0.76,
        "low": 0.52,
        "unknown": 0.35,
    }.get(output.image_summary.confidence, 0.35)

    # OCR
    if ocr_text:
        session.add(OcrDocument(
            asset_id=asset.id,
            extraction_run_id=run.id,
            full_text=ocr_text,
            confidence=overall_confidence,
        ))

    # Scene
    s = output.image_summary
    session.add(DBSceneSummary(
        asset_id=asset.id,
        extraction_run_id=run.id,
        scene_type=s.primary_scene,
        setting=s.environment_type,
        time_of_day=s.time_of_day,
        weather=output.landscape_analysis.weather_visibility_cues,
        description=s.strict_caption or "No caption generated.",
        confidence=overall_confidence,
        raw=output.model_dump(),
    ))

    # Objects
    for obj in output.objects:
        attrs: dict = {
            "count": obj.count_estimate,
            "details": obj.evidence[:3],
            "significance": obj.significance,
        }
        session.add(DBObjectDetection(
            asset_id=asset.id,
            extraction_run_id=run.id,
            label=obj.object_label,
            confidence={"high": 0.9, "medium": 0.72, "low": 0.5}.get(obj.significance, 0.5),
            attributes=attrs or None,
        ))

    # Place candidates
    for cue in output.image_summary.location_cues[:5]:
        session.add(DBPlaceCandidate(
            asset_id=asset.id,
            extraction_run_id=run.id,
            name=cue,
            country=None,
            region=None,
            place_type="location_cue",
            confidence=overall_confidence,
            source="ai",
            raw={"cue": cue, "image_summary_confidence": output.image_summary.confidence},
        ))


def _batch_state_name(value) -> str:
    text = str(value or "").strip().lower()
    if "." in text:
        text = text.split(".")[-1]
    return text


def _batch_done(state) -> bool:
    name = _batch_state_name(state)
    return any(token in name for token in ("succeeded", "failed", "cancelled", "canceled"))


def _batch_succeeded(state) -> bool:
    return "succeeded" in _batch_state_name(state)


def _build_extraction_run(asset: Asset, provider_name: str, model_name: str, execution_mode: str) -> ExtractionRun:
    stored_model_name = model_name if execution_mode == "standard" else f"{model_name} + batch"
    return ExtractionRun(
        asset_id=asset.id,
        run_type="image",
        model_provider=provider_name,
        model_name=stored_model_name,
        schema_version=SCHEMA_VERSION,
        prompt_version="image_v1",
        status="running",
        started_at=datetime.now(timezone.utc),
    )


def extract_asset(
    asset: Asset,
    session: Session,
    provider: ModelProvider,
    *,
    max_px: int = MAX_GEMINI_PX,
    max_output_tokens: int | None = DEFAULT_MAX_OUTPUT_TOKENS,
    execution_mode: str = "standard",
    jpeg_quality: int = DEFAULT_JPEG_QUALITY,
) -> ExtractionRun:
    """Run AI extraction for a single asset. Creates an ExtractionRun record."""
    run = _build_extraction_run(asset, provider.provider_name, provider.model_name, execution_mode)
    session.add(run)
    session.flush()

    path = Path(asset.canonical_path)
    if not path.exists():
        run.status = "failed"
        run.error_message = "File not found on disk"
        return run

    raw_text = ""
    try:
        img_bytes, mime = _resolve_image_bytes(asset, path, max_px=max_px, jpeg_quality=jpeg_quality)
        prompt = _load_prompt() + _ocr_context_prompt(session, asset.id) + _user_context_prompt(session, asset.id)
        effective_max_output_tokens = None if not max_output_tokens or max_output_tokens <= 0 else max_output_tokens
        result = provider.generate(prompt, img_bytes, mime, max_output_tokens=effective_max_output_tokens)
        raw_text = result.text or ""
        raw_json = _parse_json_from_response(result.text)
        output = _normalize_output(ImageExtractionOutput.model_validate(raw_json))
        _write_ai_debug_dump(asset, stage="done", raw_text=raw_text, parsed_json=raw_json)

        run.raw_output = output.model_dump()
        run.tokens_in = result.tokens_in
        run.tokens_out = result.tokens_out
        run.cost_usd = _calculate_cost(result.tokens_in, result.tokens_out, provider.model_name, execution_mode)
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
    """Batch-extract assets that are new or have newer user context than their last successful extraction."""
    stats = {"processed": 0, "failed": 0, "skipped": 0, "cancelled": 0}
    failure_examples: list[str] = []

    provider = get_provider(model_provider, model_name)
    _load_prompt()  # validate prompt loads before touching DB

    with get_session() as session:
        from sqlalchemy import and_, func, or_, select

        latest_done_subq = (
            select(
                ExtractionRun.asset_id.label("asset_id"),
                func.max(func.coalesce(ExtractionRun.finished_at, ExtractionRun.started_at)).label("latest_done_at"),
            )
            .where(ExtractionRun.status == "done")
            .group_by(ExtractionRun.asset_id)
            .subquery()
        )

        stale_done_asset_ids = (
            select(Assertion.asset_id)
            .join(latest_done_subq, latest_done_subq.c.asset_id == Assertion.asset_id)
            .where(
                Assertion.is_active == True,  # noqa: E712
                Assertion.predicate.in_(["user.place", "user.gps_coords", "user.comments"]),
                Assertion.created_at > latest_done_subq.c.latest_done_at,
            )
            .distinct()
        )

        query = (
            session.query(Asset)
            .filter(
                Asset.is_missing == False,  # noqa: E712
                Asset.media_type == "photo",
                or_(
                    ~Asset.id.in_(select(latest_done_subq.c.asset_id)),
                    Asset.id.in_(stale_done_asset_ids),
                ),
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

            run = extract_asset(
                asset,
                session,
                provider,
                max_px=max_px,
                max_output_tokens=max_output_tokens,
                execution_mode="standard",
                jpeg_quality=DEFAULT_JPEG_QUALITY,
            )
            if run.status == "done":
                stats["processed"] += 1
            else:
                stats["failed"] += 1
                if run.error_message and len(failure_examples) < 3:
                    failure_examples.append(f"{asset.filename}: {run.error_message}")

    if failure_examples:
        stats["failure_examples"] = failure_examples
    return stats


def extract_all_pending_batch(
    model_name: str = "gemini-2.5-flash-lite",
    limit: int = 50,
    max_px: int = HYPER_OPTIMIZED_MAX_PX,
    max_output_tokens: int | None = DEFAULT_MAX_OUTPUT_TOKENS,
    folder_path: str | None = None,
    should_cancel: Callable[[], bool] | None = None,
) -> dict[str, int]:
    """Submit a Gemini Batch API extraction job and persist finished responses."""
    stats = {"processed": 0, "failed": 0, "skipped": 0, "cancelled": 0}
    failure_examples: list[str] = []

    provider = get_provider("gemini", model_name)
    if not hasattr(provider, "create_batch"):
        raise RuntimeError("Selected Gemini provider does not support batch extraction")
    _load_prompt()

    with get_session() as session:
        from sqlalchemy import func, or_, select

        latest_done_subq = (
            select(
                ExtractionRun.asset_id.label("asset_id"),
                func.max(func.coalesce(ExtractionRun.finished_at, ExtractionRun.started_at)).label("latest_done_at"),
            )
            .where(ExtractionRun.status == "done")
            .group_by(ExtractionRun.asset_id)
            .subquery()
        )

        stale_done_asset_ids = (
            select(Assertion.asset_id)
            .join(latest_done_subq, latest_done_subq.c.asset_id == Assertion.asset_id)
            .where(
                Assertion.is_active == True,  # noqa: E712
                Assertion.predicate.in_(["user.place", "user.gps_coords", "user.comments"]),
                Assertion.created_at > latest_done_subq.c.latest_done_at,
            )
            .distinct()
        )

        query = (
            session.query(Asset)
            .filter(
                Asset.is_missing == False,  # noqa: E712
                Asset.media_type == "photo",
                or_(
                    ~Asset.id.in_(select(latest_done_subq.c.asset_id)),
                    Asset.id.in_(stale_done_asset_ids),
                ),
            )
        )
        if folder_path:
            query = query.filter(
                (Asset.canonical_path == folder_path) | (Asset.canonical_path.like(f"{folder_path}/%"))
            )
        assets = query.limit(limit).all()

        batch_requests = []
        asset_map: dict[str, Asset] = {}
        for asset in assets:
            if should_cancel and should_cancel():
                stats["cancelled"] = 1
                break
            ext = Path(asset.canonical_path).suffix.lower()
            if ext not in SUPPORTED_IMAGE_EXT:
                stats["skipped"] += 1
                continue
            path = Path(asset.canonical_path)
            if not path.exists():
                stats["failed"] += 1
                if len(failure_examples) < 3:
                    failure_examples.append(f"{asset.filename}: File not found on disk")
                continue
            try:
                img_bytes, mime = _resolve_image_bytes(
                    asset,
                    path,
                    max_px=max_px,
                    jpeg_quality=HYPER_OPTIMIZED_JPEG_QUALITY,
                )
                prompt = _load_prompt() + _ocr_context_prompt(session, asset.id) + _user_context_prompt(session, asset.id)
                batch_requests.append(
                    provider.build_batch_request(
                        prompt=prompt,
                        image_bytes=img_bytes,
                        mime_type=mime,
                        max_output_tokens=max_output_tokens,
                        metadata={"asset_id": asset.id, "filename": asset.filename},
                    )
                )
                asset_map[asset.id] = asset
            except Exception as exc:
                logger.exception("Failed to prepare batch request for %s", asset.id)
                stats["failed"] += 1
                if len(failure_examples) < 3:
                    failure_examples.append(f"{asset.filename}: {str(exc)[:180]}")

        if not batch_requests or stats["cancelled"]:
            if failure_examples:
                stats["failure_examples"] = failure_examples
            return stats

        batch = provider.create_batch(
            batch_requests,
            display_name=f"fmo-image-extract-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}",
        )
        batch_name = getattr(batch, "name", None)
        if not batch_name:
            raise RuntimeError("Gemini Batch API did not return a batch job name")

        while True:
            if should_cancel and should_cancel():
                provider.cancel_batch(batch_name)
                stats["cancelled"] = 1
                break
            batch = provider.get_batch(batch_name)
            state = getattr(batch, "state", None)
            if _batch_done(state):
                break
            import time
            time.sleep(5)

        if stats["cancelled"]:
            if failure_examples:
                stats["failure_examples"] = failure_examples
            return stats

        if not _batch_succeeded(getattr(batch, "state", None)):
            error = getattr(batch, "error", None)
            raise RuntimeError(f"Gemini batch job did not succeed: {error or getattr(batch, 'state', 'unknown')}")

        inlined_responses = []
        dest = getattr(batch, "dest", None)
        if dest is not None:
            inlined_responses = getattr(dest, "inlinedResponses", None) or getattr(dest, "inlined_responses", None) or []

        for item in inlined_responses:
            metadata = getattr(item, "metadata", None) or {}
            asset_id = metadata.get("asset_id") if isinstance(metadata, dict) else None
            if not asset_id or asset_id not in asset_map:
                continue
            asset = asset_map[asset_id]
            run = _build_extraction_run(asset, "gemini", model_name, "batch")
            session.add(run)
            session.flush()
            raw_text = ""
            try:
                if getattr(item, "error", None):
                    raise RuntimeError(str(item.error))
                result = provider.parse_batch_response(item)
                raw_text = result.text or ""
                raw_json = _parse_json_from_response(raw_text)
                output = _normalize_output(ImageExtractionOutput.model_validate(raw_json))
                _write_ai_debug_dump(asset, stage="done", raw_text=raw_text, parsed_json=raw_json)
                run.raw_output = output.model_dump()
                run.tokens_in = result.tokens_in
                run.tokens_out = result.tokens_out
                run.cost_usd = _calculate_cost(result.tokens_in, result.tokens_out, model_name, "batch")
                run.status = "done"
                run.finished_at = datetime.now(timezone.utc)
                _persist_results(session, asset, run, output)
                stats["processed"] += 1
            except ValidationError as exc:
                run.status = "failed"
                run.error_message = f"Schema validation failed: {exc.error_count()} error(s)"
                run.finished_at = datetime.now(timezone.utc)
                if raw_text:
                    run.raw_output = _failure_debug_payload(raw_text, str(exc), "schema")
                _write_ai_debug_dump(asset, stage="schema_failed", raw_text=raw_text, error_message=str(exc))
                stats["failed"] += 1
                if len(failure_examples) < 3:
                    failure_examples.append(f"{asset.filename}: {run.error_message}")
            except Exception as exc:
                run.status = "failed"
                run.error_message = _summarize_parse_error(str(exc), raw_text)
                run.finished_at = datetime.now(timezone.utc)
                if raw_text:
                    debug_stage = "truncated" if _looks_truncated_response(raw_text) else "parse"
                    run.raw_output = _failure_debug_payload(raw_text, str(exc), debug_stage)
                _write_ai_debug_dump(asset, stage="parse_failed", raw_text=raw_text, error_message=str(exc))
                stats["failed"] += 1
                if len(failure_examples) < 3:
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
