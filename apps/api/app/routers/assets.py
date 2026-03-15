from __future__ import annotations

import re

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.core.db import get_session

router = APIRouter(tags=["assets"])


class AssetListItem(BaseModel):
    id: str
    filename: str
    type: str
    date: str | None = None
    captured_at: str | None = None
    folder_path: str | None = None
    lat: float | None = None
    lon: float | None = None
    has_ocr: bool = False
    has_gps: bool = False
    is_duplicate: bool = False
    thumbnail_url: str | None = None
    width: int | None = None
    height: int | None = None
    scene_label: str | None = None
    place_label: str | None = None
    object_labels: list[str] = []
    tags: list[str] = []
    summary: str | None = None
    extraction_status: str | None = None
    confidence_label: str | None = None
    review_bucket: str | None = None


class AssetListResponse(BaseModel):
    items: list[AssetListItem]
    total: int
    page: int
    page_size: int


# ── Rich detail schema ─────────────────────────────────────────────────────────

class MediaInfo(BaseModel):
    width: int | None = None
    height: int | None = None
    duration_seconds: float | None = None
    codec: str | None = None
    color_space: str | None = None
    camera_make: str | None = None
    camera_model: str | None = None
    lens_model: str | None = None
    aperture: float | None = None
    shutter_speed: str | None = None
    iso: int | None = None
    focal_length: float | None = None
    flash: str | None = None
    orientation: int | None = None
    raw_exif: dict | None = None

class LocationInfo(BaseModel):
    lat: float | None = None
    lon: float | None = None
    altitude: float | None = None
    country: str | None = None
    city: str | None = None

class TemporalInfo(BaseModel):
    best_timestamp: str | None = None
    source: str | None = None
    confidence: str | None = None
    has_conflict: bool = False
    exif_datetime: str | None = None
    gps_datetime: str | None = None
    filesystem_mtime: str | None = None
    video_creation_time: str | None = None

class SceneInfo(BaseModel):
    setting: str | None = None
    time_of_day: str | None = None
    weather: str | None = None
    description: str | None = None
    confidence: float | None = None

class PlaceInfo(BaseModel):
    name: str | None = None
    country: str | None = None
    region: str | None = None
    place_type: str | None = None
    confidence: float | None = None
    source: str | None = None

class ObjectInfo(BaseModel):
    label: str
    confidence: float | None = None
    count: int | None = None
    color: str | None = None
    details: list[str] = []


class TagInfo(BaseModel):
    label: str
    confidence: float | None = None

class AssetDetail(BaseModel):
    id: str
    filename: str
    canonical_path: str
    type: str
    file_size_bytes: int | None = None
    thumbnail_url: str | None = None
    large_thumbnail_url: str | None = None
    keyframe_urls: list[str] = []
    temporal: TemporalInfo | None = None
    location: LocationInfo | None = None
    media_info: MediaInfo | None = None
    ocr_text: str | None = None
    scene: SceneInfo | None = None
    objects: list[ObjectInfo] = []
    place_candidates: list[PlaceInfo] = []
    summary: str | None = None
    tags: list[str] = []
    tag_details: list[TagInfo] = []
    artistic_notes: "ArtisticNotesInfo | None" = None
    extraction_notes: str | None = None
    analysis: dict | None = None
    location_meta: "LocationMetaInfo | None" = None
    user_context: "UserContextInfo | None" = None
    series: "SeriesInfo | None" = None
    extraction_status: str | None = None
    extraction_run: "ExtractionRunInfo | None" = None


class ExtractionRunInfo(BaseModel):
    id: str
    model_provider: str | None = None
    model_name: str | None = None
    prompt_version: str | None = None
    schema_version: str | None = None
    status: str
    started_at: str | None = None
    finished_at: str | None = None
    tokens_in: int | None = None
    tokens_out: int | None = None
    cost_usd: float | None = None
    error_message: str | None = None
    debug_stage: str | None = None
    debug_excerpt: str | None = None


class ArtisticNotesInfo(BaseModel):
    summary: str | None = None
    composition: str | None = None
    lighting: str | None = None
    detail: str | None = None
    resolution: str | None = None


class LocationMetaInfo(BaseModel):
    place_name_candidate: str | None = None
    nearest_city_candidate: str | None = None
    province_or_state_candidate: str | None = None
    country_candidate: str | None = None
    location_source: str = "unknown"
    location_precision: str = "unknown"
    location_confidence: str = "low"
    location_evidence: list[str] = []


class UserContextInfo(BaseModel):
    place: str | None = None
    gps_coords: str | None = None
    comments: str | None = None


class SeriesItem(BaseModel):
    id: str
    filename: str
    captured_at: str | None = None


class SeriesInfo(BaseModel):
    label: str
    count: int
    items: list[SeriesItem]


class FolderItem(BaseModel):
    path: str
    count: int


class FolderResponse(BaseModel):
    items: list[FolderItem]


class ResetMetadataRequest(BaseModel):
    folder_path: str


class ResetMetadataResponse(BaseModel):
    folder_path: str
    asset_count: int


class UpdateUserContextRequest(BaseModel):
    place: str | None = None
    gps_coords: str | None = None
    comments: str | None = None


class ReviewQueueItem(BaseModel):
    name: str
    label: str
    description: str
    count: int
    items: list[AssetListItem]


class ReviewQueueResponse(BaseModel):
    queues: list[ReviewQueueItem]


def _iso(dt) -> str | None:
    return dt.isoformat() if dt else None


def _latest_run(asset, successful_only: bool = False):
    runs = sorted(
        asset.extraction_runs or [],
        key=lambda run: run.started_at or 0,
        reverse=True,
    )
    if successful_only:
        runs = [run for run in runs if run.status == "done"]
    return runs[0] if runs else None


def _latest_scene(run):
    scenes = sorted(run.scene_summaries or [], key=lambda item: item.created_at or 0, reverse=True)
    return scenes[0] if scenes else None


def _latest_ocr(run):
    docs = sorted(run.ocr_documents or [], key=lambda item: item.created_at or 0, reverse=True)
    return docs[0] if docs else None


def _relative_folder(asset) -> str:
    from pathlib import Path as _Path

    root = _Path(asset.source_root or "")
    try:
        folder = str(_Path(asset.canonical_path).relative_to(root).parent)
    except Exception:
        folder = str(_Path(asset.canonical_path).parent)
    folder = folder.replace("\\", "/")
    return "/" if folder in ("", ".") else folder


def _tags_for_asset(asset, run=None, scene=None, ocr=None, places=None, objects=None) -> list[str]:
    import re

    tags: list[str] = []
    raw = run.raw_output if run and isinstance(run.raw_output, dict) else {}
    summary = raw.get("image_summary") if isinstance(raw.get("image_summary"), dict) else {}
    setting_analysis = raw.get("setting_analysis") if isinstance(raw.get("setting_analysis"), dict) else {}
    operational = raw.get("operational_context") if isinstance(raw.get("operational_context"), dict) else {}
    landscape = raw.get("landscape_analysis") if isinstance(raw.get("landscape_analysis"), dict) else {}

    candidate_values = [
        summary.get("primary_scene"),
        summary.get("time_of_day"),
        *list(summary.get("secondary_scenes") or []),
        *list(summary.get("location_cues") or []),
        *list(setting_analysis.get("visible_logos") or []),
        *list(setting_analysis.get("visible_insignia") or []),
        *list(setting_analysis.get("organization_text_cues") or []),
        landscape.get("terrain_type"),
        landscape.get("weather_visibility_cues"),
        *list(operational.get("damage_indicators") or []),
    ]
    for value in candidate_values:
        if value:
            cleaned = str(value).strip().lower()
            if cleaned not in tags:
                tags.append(cleaned)
    for obj in (objects or [])[:6]:
        cleaned = obj.label.strip().lower()
        if cleaned and cleaned not in tags:
            tags.append(cleaned)
    if ocr and ocr.full_text:
        phrases = re.findall(r"[A-Za-z0-9][A-Za-z0-9'&.-]{2,}", ocr.full_text)
        for phrase in phrases[:8]:
            cleaned = phrase.strip().lower()
            if cleaned not in tags:
                tags.append(cleaned)
            if len(tags) >= 10:
                break
    return tags[:10]


def _tag_details_for_run(run, scene=None, places=None, objects=None) -> list[TagInfo]:
    raw = run.raw_output if run and isinstance(run.raw_output, dict) else {}
    items: list[TagInfo] = []
    seen: set[str] = set()
    confidence_map = {"high": 0.92, "medium": 0.76, "low": 0.52, "unknown": None}
    summary = raw.get("image_summary") if isinstance(raw.get("image_summary"), dict) else {}
    setting_analysis = raw.get("setting_analysis") if isinstance(raw.get("setting_analysis"), dict) else {}
    operational = raw.get("operational_context") if isinstance(raw.get("operational_context"), dict) else {}
    landscape = raw.get("landscape_analysis") if isinstance(raw.get("landscape_analysis"), dict) else {}

    structured_tags: list[tuple[str, float | None]] = []
    for value in (
        [summary.get("primary_scene"), summary.get("time_of_day"), landscape.get("terrain_type"), landscape.get("weather_visibility_cues")]
        + list(summary.get("secondary_scenes") or [])
        + list(summary.get("location_cues") or [])
        + list(setting_analysis.get("visible_logos") or [])
        + list(setting_analysis.get("visible_insignia") or [])
        + list(setting_analysis.get("organization_text_cues") or [])
        + list(operational.get("damage_indicators") or [])
    ):
        if isinstance(value, str):
            structured_tags.append((value.strip().lower(), confidence_map.get(summary.get("confidence"))))

    for label, confidence in structured_tags:
        if label and label not in seen:
            items.append(TagInfo(label=label, confidence=confidence))
            seen.add(label)

    fallback_values = [
        scene.setting if scene else None,
        scene.time_of_day if scene else None,
        scene.weather if scene else None,
        places[0].name if places else None,
    ]
    for value in fallback_values:
        if value:
            label = str(value).strip().lower()
            if label and label not in seen:
                items.append(TagInfo(label=label, confidence=None))
                seen.add(label)

    for obj in (objects or [])[:5]:
        label = obj.label.strip().lower()
        if label and label not in seen:
            items.append(TagInfo(label=label, confidence=obj.confidence))
            seen.add(label)

    return items[:12]


def _summary_for_asset(run, scene, places, objects) -> str | None:
    raw = run.raw_output if run and isinstance(run.raw_output, dict) else {}
    image_summary = raw.get("image_summary") if isinstance(raw.get("image_summary"), dict) else {}
    if isinstance(image_summary.get("strict_caption"), str) and image_summary.get("strict_caption").strip():
        return _clean_summary_text(image_summary["strict_caption"].strip())
    parts = []
    if scene and scene.description:
        parts.append(scene.description.split(".")[0].strip())
    if places:
        parts.append(f"Likely place: {places[0].name}.")
    elif objects:
        parts.append(f"Main subjects: {', '.join(obj.label for obj in objects[:3])}.")
    summary = " ".join(part for part in parts if part)
    return _clean_summary_text(summary) if summary else None


def _clean_summary_text(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    match = re.search(r"(Main subjects:\s*)(.+)$", cleaned, flags=re.IGNORECASE)
    if match:
        prefix, subjects = match.groups()
        deduped = _dedupe_text_items(subjects)
        cleaned = f"{cleaned[:match.start()]}{prefix}{deduped}".strip()
    return cleaned


def _contextualize_summary(
    summary: str | None,
    user_context: UserContextInfo | None,
    location_meta: LocationMetaInfo | None,
    analysis: dict | None,
) -> str | None:
    parts: list[str] = []
    if summary:
        parts.append(_clean_summary_text(summary))

    context_bits: list[str] = []
    if user_context and user_context.place:
        context_bits.append(f"Archive place note: {user_context.place}.")

    if location_meta:
        loc_parts = [
            location_meta.place_name_candidate,
            location_meta.nearest_city_candidate,
            location_meta.province_or_state_candidate,
            location_meta.country_candidate,
        ]
        loc_text = ", ".join(part for part in loc_parts if part)
        if loc_text:
            context_bits.append(f"Location context: {loc_text}.")

    if user_context and user_context.comments:
        context_bits.append(f"Archive note: {user_context.comments}")

    if analysis and isinstance(analysis, dict):
        operational = analysis.get("operational_context") if isinstance(analysis.get("operational_context"), dict) else {}
        functions = operational.get("scene_function_hypotheses") if isinstance(operational, dict) else []
        if isinstance(functions, list) and functions:
            labels: list[str] = []
            for item in functions[:2]:
                if isinstance(item, dict) and item.get("label"):
                    labels.append(str(item["label"]).replace("_", " "))
            if labels:
                context_bits.append(f"Operational context: {', '.join(dict.fromkeys(labels))}.")

    for bit in context_bits:
        cleaned = _clean_summary_text(bit)
        if cleaned and cleaned not in parts:
            parts.append(cleaned)

    if not parts:
        return None
    return " ".join(parts)


def _dedupe_text_items(value: str) -> str:
    items = [item.strip(" .") for item in value.split(",")]
    output: list[str] = []
    seen_again: set[str] = set()
    for item in items:
        normalized = item.lower()
        if item and normalized not in seen_again:
            output.append(item)
            seen_again.add(normalized)
    return ", ".join(output)


def _normalized_objects(objs) -> list[ObjectInfo]:
    merged: dict[tuple[str, str | None], ObjectInfo] = {}
    for obj in objs:
        attrs = obj.attributes or {}
        details = [str(detail).strip() for detail in (attrs.get("details") or []) if str(detail).strip()]
        color = str(attrs.get("color")).strip() if attrs.get("color") else None
        key = (obj.label.strip().lower(), color.lower() if color else None)
        if key not in merged:
            merged[key] = ObjectInfo(
                label=obj.label,
                confidence=obj.confidence,
                count=attrs.get("count") if attrs else None,
                color=color,
                details=details[:3],
            )
            continue

        existing = merged[key]
        existing.confidence = max(existing.confidence or 0, obj.confidence or 0) or existing.confidence
        existing.count = max(existing.count or 1, attrs.get("count") or 1)
        existing.details = list(dict.fromkeys([*existing.details, *details]))[:3]
    return list(merged.values())


def _artistic_notes(run) -> ArtisticNotesInfo | None:
    raw = run.raw_output if run and isinstance(run.raw_output, dict) else {}
    notes = raw.get("quality_review") if isinstance(raw.get("quality_review"), dict) else None
    if not isinstance(notes, dict):
        return None
    return ArtisticNotesInfo(
        summary=_norm_phrase(f"Quality: {notes.get('image_quality')}" if notes.get("image_quality") else None),
        composition=_norm_phrase(f"Framing: {notes.get('framing')}" if notes.get("framing") else None),
        lighting=None,
        detail=_norm_phrase(f"Occlusion: {notes.get('occlusion_level')}" if notes.get("occlusion_level") else None),
        resolution=_norm_phrase("; ".join(notes.get("limitations") or []) if notes.get("limitations") else None),
    )


def _extraction_notes(run) -> str | None:
    raw = run.raw_output if run and isinstance(run.raw_output, dict) else {}
    quality = raw.get("quality_review") if isinstance(raw.get("quality_review"), dict) else {}
    limitations = quality.get("limitations") if isinstance(quality, dict) else []
    if limitations:
        return "Limits: " + ", ".join(str(item) for item in limitations[:4])
    return None


def _norm_phrase(value: str | None) -> str | None:
    if not value or not isinstance(value, str):
        return None
    cleaned = re.sub(r"\s+", " ", value).strip()
    return cleaned or None


def _user_context_for_asset(session, asset_id: str) -> UserContextInfo | None:
    from sqlalchemy import select as sa_select
    from models import Assertion

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
        if key in values and values[key] is None:
            values[key] = _norm_phrase(row.value)

    if not any(values.values()):
        return None
    return UserContextInfo(**values)


def _location_meta(asset, run, ocr_text: str | None, places: list[PlaceInfo]) -> LocationMetaInfo | None:
    raw = run.raw_output if run and isinstance(run.raw_output, dict) else {}
    image_summary = raw.get("image_summary") if isinstance(raw.get("image_summary"), dict) else {}
    model_location_meta = raw.get("location_meta") if isinstance(raw.get("location_meta"), dict) else {}
    location_cues = [str(item).strip() for item in image_summary.get("location_cues") or [] if str(item).strip()]
    best_place = max(places, key=lambda item: item.confidence or 0, default=None)
    evidence: list[str] = [str(item).strip() for item in model_location_meta.get("location_evidence") or [] if str(item).strip()]

    place_name_candidate = _norm_phrase(model_location_meta.get("place_name_candidate"))
    nearest_city_candidate = _norm_phrase(model_location_meta.get("nearest_city_candidate"))
    province_candidate = _norm_phrase(model_location_meta.get("province_or_state_candidate"))
    country_candidate = _norm_phrase(model_location_meta.get("country_candidate"))
    location_source = str(model_location_meta.get("location_source") or "unknown")
    location_precision = str(model_location_meta.get("location_precision") or "unknown")
    location_confidence = str(model_location_meta.get("location_confidence") or "low")

    if asset.location and asset.location.latitude is not None and asset.location.longitude is not None:
        evidence.append("embedded coordinates available")
        if location_source == "unknown":
            location_source = "embedded_metadata"
        if location_confidence == "low":
            location_confidence = "medium"

    if best_place:
        if best_place.name and not place_name_candidate:
            place_name_candidate = best_place.name
        if best_place.place_type in {"city", "town"} and best_place.name and not nearest_city_candidate:
            nearest_city_candidate = best_place.name
        if best_place.region and not province_candidate:
            province_candidate = best_place.region
        if best_place.country and not country_candidate:
            country_candidate = best_place.country

        if ocr_text and best_place.name and best_place.name.lower() in ocr_text.lower():
            location_source = "combined" if location_source != "unknown" else "ocr_text"
            evidence.append("place cue also appears in visible text")
            location_confidence = "high" if asset.location else "medium"
        elif best_place.source == "gps":
            location_source = "embedded_metadata"
            evidence.append("place candidate linked to coordinate-derived record")
            location_confidence = "high"
        elif best_place.source == "ai":
            if location_source == "embedded_metadata":
                location_source = "combined"
                evidence.append("visual place cue aligned with embedded coordinates")
                location_confidence = "high"
            else:
                location_source = "landmark_visual_inference"
                evidence.append("candidate place inferred from visible landmark or scene cues")
                location_confidence = "medium" if (best_place.confidence or 0) >= 0.85 else "low"

        if location_precision == "unknown" and place_name_candidate:
            location_precision = "site_level" if best_place.place_type not in {"city", "town"} else "city_level"
        elif location_precision == "unknown" and nearest_city_candidate:
            location_precision = "city_level"
        elif location_precision == "unknown" and province_candidate:
            location_precision = "province_or_state_level"
        elif location_precision == "unknown" and country_candidate:
            location_precision = "country_level"

    if not best_place and location_cues:
        location_source = "landmark_visual_inference" if location_source == "unknown" else location_source
        location_precision = "place_type_only" if location_precision == "unknown" else location_precision
        location_confidence = "low" if location_confidence == "low" else location_confidence
        evidence.extend(location_cues[:4])

    if not evidence and not any([place_name_candidate, nearest_city_candidate, province_candidate, country_candidate]):
        return None

    return LocationMetaInfo(
        place_name_candidate=place_name_candidate,
        nearest_city_candidate=nearest_city_candidate,
        province_or_state_candidate=province_candidate,
        country_candidate=country_candidate,
        location_source=location_source,
        location_precision=location_precision,
        location_confidence=location_confidence,
        location_evidence=list(dict.fromkeys(evidence))[:5],
    )


def _confidence_label(value: float | None) -> str | None:
    if value is None:
        return None
    if value >= 0.86:
        return "high"
    if value >= 0.72:
        return "medium"
    return "low"


def _review_bucket(asset) -> str | None:
    latest_done = _latest_run(asset, successful_only=True)
    if latest_done is None:
        return "needs-extraction"
    if asset.temporal and asset.temporal.has_conflict:
        return "timestamp-conflict"
    scene = _latest_scene(latest_done)
    if scene and scene.confidence is not None and scene.confidence < 0.72:
        return "low-confidence"
    if asset.location is not None and not (latest_done.place_candidates or []):
        return "location-unverified"
    return None


def _asset_to_list_item(asset) -> AssetListItem:
    latest_done = _latest_run(asset, successful_only=True)
    latest_any = _latest_run(asset)
    scene = _latest_scene(latest_done) if latest_done else None
    ocr = _latest_ocr(latest_done) if latest_done else None
    places = latest_done.place_candidates if latest_done else []
    objects = latest_done.object_detections if latest_done else []
    best_place = max(places, key=lambda item: item.confidence or 0, default=None)
    summary = _summary_for_asset(latest_done, scene, places, objects)
    tags = _tags_for_asset(asset, latest_done, scene, ocr, places, objects)

    return AssetListItem(
        id=asset.id,
        filename=asset.filename,
        type=asset.media_type,
        date=asset.temporal.best_timestamp.date().isoformat() if asset.temporal and asset.temporal.best_timestamp else None,
        captured_at=_iso(asset.temporal.best_timestamp if asset.temporal else None),
        folder_path=_relative_folder(asset),
        lat=asset.location.latitude if asset.location else None,
        lon=asset.location.longitude if asset.location else None,
        has_gps=asset.location is not None,
        has_ocr=bool(ocr and ocr.full_text),
        width=asset.media_info.width if asset.media_info else None,
        height=asset.media_info.height if asset.media_info else None,
        thumbnail_url=f"/api/assets/{asset.id}/thumbnail" if asset.thumbnails or asset.keyframes else None,
        scene_label=(scene.setting or scene.scene_type) if scene else None,
        place_label=best_place.name if best_place else None,
        object_labels=[obj.label for obj in objects[:4]],
        tags=tags,
        summary=summary,
        extraction_status=latest_any.status if latest_any else None,
        confidence_label=_confidence_label(scene.confidence if scene else (ocr.confidence if ocr else None)),
        review_bucket=_review_bucket(asset),
    )


@router.get("", response_model=AssetListResponse)
async def list_assets(
    q: str | None = Query(None, description="Full-text search query"),
    ai_text: str | None = Query(None, description="Full-text search across AI extraction output"),
    scene: str | None = Query(None),
    place: str | None = Query(None),
    object_label: str | None = Query(None, alias="object"),
    match_mode: str = Query("any", alias="match"),
    folder: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(48, ge=1, le=200),
    asset_type: str | None = Query(None, alias="type"),
    has_ocr: bool | None = Query(None),
    has_gps: bool | None = Query(None),
    has_ai: bool | None = Query(None),
    review_bucket: str | None = Query(None),
) -> AssetListResponse:
    from repositories.assets import list_assets as db_list_assets

    with get_session() as session:
        assets, total = db_list_assets(
            session,
            media_type=asset_type,
            search=q,
            ai_text=ai_text,
            scene=scene,
            place=place,
            object_label=object_label,
            match_mode=match_mode,
            folder=folder,
            has_ocr=has_ocr,
            has_gps=has_gps,
            has_ai=has_ai,
            review_bucket=review_bucket,
            page=page,
            page_size=page_size,
        )
        items = [_asset_to_list_item(a) for a in assets]
    return AssetListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{asset_id}/thumbnail")
async def get_thumbnail(asset_id: str, size: str = "small"):
    """Serve the thumbnail JPEG for an asset.

    ?size=small  → 400px (default, for gallery)
    ?size=large  → largest stored thumb (for detail view / AI analysis)
    Falls back to first keyframe for video.
    """
    import uuid as _uuid
    from models import Asset

    try:
        _uuid.UUID(asset_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Asset not found")

    with get_session() as session:
        asset = session.get(Asset, asset_id)
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")

        if asset.thumbnails:
            thumbs = sorted(asset.thumbnails, key=lambda t: t.width)
            from pathlib import Path as _Path
            if size == "large":
                thumb = thumbs[-1]
            else:
                preferred = next((item for item in thumbs if item.width >= 640), None)
                thumb = preferred or thumbs[-1]
            if _Path(thumb.path).exists():
                return FileResponse(thumb.path, media_type="image/jpeg")

        # Fall back to first keyframe
        if asset.keyframes:
            kf = sorted(asset.keyframes, key=lambda k: k.sequence_index)[0]
            from pathlib import Path as _Path
            if _Path(kf.path).exists():
                return FileResponse(kf.path, media_type="image/jpeg")


@router.get("/folders", response_model=FolderResponse)
async def get_folders(
    q: str | None = Query(None),
    ai_text: str | None = Query(None),
    scene: str | None = Query(None),
    place: str | None = Query(None),
    object_label: str | None = Query(None, alias="object"),
    match_mode: str = Query("any", alias="match"),
    folder: str | None = Query(None),
    asset_type: str | None = Query(None, alias="type"),
    has_ocr: bool | None = Query(None),
    has_gps: bool | None = Query(None),
    has_ai: bool | None = Query(None),
    review_bucket: str | None = Query(None),
) -> FolderResponse:
    from repositories.assets import list_folders as db_list_folders

    with get_session() as session:
        items = db_list_folders(
            session,
            folder_prefix=folder,
            media_type=asset_type,
            search=q,
            ai_text=ai_text,
            scene=scene,
            place=place,
            object_label=object_label,
            match_mode=match_mode,
            has_ocr=has_ocr,
            has_gps=has_gps,
            has_ai=has_ai,
            review_bucket=review_bucket,
        )
    return FolderResponse(items=[FolderItem(path=path, count=count) for path, count in items])


@router.post("/reset-metadata", response_model=ResetMetadataResponse)
async def reset_metadata(body: ResetMetadataRequest) -> ResetMetadataResponse:
    from sqlalchemy import delete as sa_delete, select as sa_select
    from models import (
        Asset,
        AssetLocation,
        AssetMediaInfo,
        AssetTemporal,
        AssetThumbnail,
        Assertion,
        ExtractionRun,
        Keyframe,
        OcrDocument,
        ObjectDetection,
        PlaceCandidate,
        ReviewAction,
        SceneSummary,
    )

    folder = body.folder_path.strip()
    if not folder:
        raise HTTPException(status_code=422, detail="folder_path is required")

    with get_session() as session:
        asset_ids = session.scalars(
            sa_select(Asset.id).where(
                (Asset.canonical_path == folder) | (Asset.canonical_path.like(f"{folder}/%"))
            )
        ).all()
        if not asset_ids:
            return ResetMetadataResponse(folder_path=folder, asset_count=0)

        for table in (
            ReviewAction,
            Assertion,
            OcrDocument,
            ObjectDetection,
            PlaceCandidate,
            SceneSummary,
            ExtractionRun,
            AssetThumbnail,
            Keyframe,
            AssetLocation,
            AssetTemporal,
            AssetMediaInfo,
        ):
            session.execute(sa_delete(table).where(table.asset_id.in_(asset_ids)))

        return ResetMetadataResponse(folder_path=folder, asset_count=len(asset_ids))

    raise HTTPException(status_code=404, detail="No thumbnail generated yet")


@router.get("/{asset_id}/detail", response_model=AssetDetail)
async def get_asset_detail(asset_id: str) -> AssetDetail:
    """Full detail including enrichment, AI extraction results."""
    import uuid as _uuid
    from models import Asset, OcrDocument, SceneSummary, ObjectDetection, PlaceCandidate, ExtractionRun, AssetTemporal

    try:
        _uuid.UUID(asset_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Asset not found")

    with get_session() as session:
        asset = session.get(Asset, asset_id)
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")

        # Thumbnail/keyframe URLs
        thumb_url = None
        large_thumb_url = None
        kf_urls: list[str] = []
        if asset.thumbnails:
            thumb_url = f"/api/assets/{asset_id}/thumbnail"
            large_thumb_url = f"/api/assets/{asset_id}/thumbnail?size=large"
        if asset.keyframes:
            kf_urls = [f"/api/assets/{asset_id}/thumbnail"]  # first keyframe via same endpoint

        # Temporal
        temp = None
        if asset.temporal:
            t = asset.temporal
            temp = TemporalInfo(
                best_timestamp=_iso(t.best_timestamp),
                source=t.best_timestamp_source,
                confidence=t.best_timestamp_confidence,
                has_conflict=t.has_conflict or False,
                exif_datetime=_iso(t.exif_datetime),
                gps_datetime=_iso(t.gps_datetime),
                filesystem_mtime=_iso(t.filesystem_mtime),
                video_creation_time=_iso(t.video_creation_time),
            )

        # Location
        loc = None
        if asset.location:
            l = asset.location
            loc = LocationInfo(lat=l.latitude, lon=l.longitude, altitude=l.altitude_m)

        # Media info — map DB columns to schema (raw EXIF fields come from exiftool_raw)
        mi = None
        if asset.media_info:
            m = asset.media_info
            exif = m.exiftool_raw or {}
            lens_model = exif.get("LensModel") or exif.get("Lens")
            mi = MediaInfo(
                width=m.width, height=m.height,
                duration_seconds=m.duration_seconds,
                codec=m.video_codec,
                camera_make=m.make,
                camera_model=m.model,
                lens_model=str(lens_model) if lens_model is not None else None,
                aperture=exif.get("Aperture") or exif.get("FNumber"),
                shutter_speed=str(exif.get("ShutterSpeed") or exif.get("ExposureTime") or ""),
                iso=exif.get("ISO"),
                focal_length=exif.get("FocalLength"),
                flash=str(exif.get("Flash") or ""),
                orientation=exif.get("Orientation"),
                raw_exif=exif if exif else None,
            )

        # Latest successful extraction run
        from sqlalchemy import select as sa_select
        run = session.scalar(
            sa_select(ExtractionRun)
            .where(ExtractionRun.asset_id == asset_id, ExtractionRun.status == "done")
            .order_by(ExtractionRun.started_at.desc())
        )

        ocr_text = None
        scene = None
        objects: list[ObjectInfo] = []
        places: list[PlaceInfo] = []
        summary = None
        tags: list[str] = []
        tag_details: list[TagInfo] = []
        artistic_notes = None
        extraction_notes = None
        extraction_status = None
        analysis = None
        location_meta = None
        user_context = _user_context_for_asset(session, asset_id)

        extraction_run = None
        if run:
            extraction_status = run.status
            extraction_run = ExtractionRunInfo(
                id=run.id,
                model_provider=run.model_provider,
                model_name=run.model_name,
                prompt_version=run.prompt_version,
                schema_version=run.schema_version,
                status=run.status,
                started_at=_iso(run.started_at),
                finished_at=_iso(run.finished_at),
                tokens_in=run.tokens_in,
                tokens_out=run.tokens_out,
                cost_usd=run.cost_usd,
                error_message=run.error_message,
                debug_stage=run.raw_output.get("debug_stage") if isinstance(run.raw_output, dict) else None,
                debug_excerpt=run.raw_output.get("debug_excerpt") if isinstance(run.raw_output, dict) else None,
            )
            # OCR
            ocr_doc = session.scalar(
                sa_select(OcrDocument).where(OcrDocument.extraction_run_id == run.id)
            )
            if ocr_doc:
                ocr_text = ocr_doc.full_text

            # Scene
            sc = session.scalar(
                sa_select(SceneSummary).where(SceneSummary.extraction_run_id == run.id)
            )
            if sc:
                scene = SceneInfo(
                    setting=sc.scene_type,
                    time_of_day=sc.time_of_day,
                    weather=sc.weather,
                    description=sc.description,
                    confidence=sc.confidence,
                )

            # Objects
            objs = session.scalars(
                sa_select(ObjectDetection).where(ObjectDetection.extraction_run_id == run.id)
            ).all()
            objects = _normalized_objects(objs)

            # Places
            pcs = session.scalars(
                sa_select(PlaceCandidate).where(PlaceCandidate.extraction_run_id == run.id)
            ).all()
            places = [PlaceInfo(name=p.name, country=p.country, region=p.region, place_type=p.place_type, confidence=p.confidence, source=p.source) for p in pcs]
            summary = _summary_for_asset(run, scene, places, objects)
            tags = _tags_for_asset(asset, run, scene, ocr_doc, places, objects)
            tag_details = _tag_details_for_run(run, scene, places, objects)
            artistic_notes = _artistic_notes(run)
            extraction_notes = _extraction_notes(run)
            analysis = run.raw_output if isinstance(run.raw_output, dict) else None
            location_meta = _location_meta(asset, run, ocr_text, places)
        else:
            # Check if extraction was attempted but failed
            any_run = session.scalar(
                sa_select(ExtractionRun)
                .where(ExtractionRun.asset_id == asset_id)
                .order_by(ExtractionRun.started_at.desc())
            )
            if any_run:
                extraction_status = any_run.status
                extraction_run = ExtractionRunInfo(
                    id=any_run.id,
                    model_provider=any_run.model_provider,
                    model_name=any_run.model_name,
                    prompt_version=any_run.prompt_version,
                    schema_version=any_run.schema_version,
                    status=any_run.status,
                    started_at=_iso(any_run.started_at),
                    finished_at=_iso(any_run.finished_at),
                    tokens_in=any_run.tokens_in,
                    tokens_out=any_run.tokens_out,
                    cost_usd=any_run.cost_usd,
                    error_message=any_run.error_message,
                    debug_stage=any_run.raw_output.get("debug_stage") if isinstance(any_run.raw_output, dict) else None,
                    debug_excerpt=any_run.raw_output.get("debug_excerpt") if isinstance(any_run.raw_output, dict) else None,
                )

        series = None
        if asset.temporal and asset.temporal.best_timestamp:
            from pathlib import Path as _Path
            from datetime import timedelta

            asset_folder = str(_Path(asset.canonical_path).parent)
            window_start = asset.temporal.best_timestamp - timedelta(minutes=15)
            window_end = asset.temporal.best_timestamp + timedelta(minutes=15)
            neighbors = session.scalars(
                sa_select(Asset)
                .join(AssetTemporal, AssetTemporal.asset_id == Asset.id)
                .where(
                    Asset.id != asset.id,
                    Asset.is_missing == False,  # noqa: E712
                    Asset.canonical_path.like(f"{asset_folder}/%"),
                    AssetTemporal.best_timestamp >= window_start,
                    AssetTemporal.best_timestamp <= window_end,
                )
                .order_by(AssetTemporal.best_timestamp.asc())
            ).all()
            group = [
                SeriesItem(id=asset.id, filename=asset.filename, captured_at=_iso(asset.temporal.best_timestamp))
            ]
            for neighbor in neighbors:
                if len(group) >= 12:
                    break
                group.append(
                    SeriesItem(
                        id=neighbor.id,
                        filename=neighbor.filename,
                        captured_at=_iso(neighbor.temporal.best_timestamp if neighbor.temporal else None),
                    )
                )
            if len(group) > 1:
                group = sorted(group, key=lambda item: item.captured_at or "")
                series = SeriesInfo(label=f"{len(group)} photos taken close together", count=len(group), items=group)

        summary = _contextualize_summary(summary, user_context, location_meta, analysis)

        return AssetDetail(
            id=asset.id,
            filename=asset.filename,
            canonical_path=asset.canonical_path,
            type=asset.media_type,
            file_size_bytes=asset.file_size_bytes,
            thumbnail_url=thumb_url,
            large_thumbnail_url=large_thumb_url,
            keyframe_urls=kf_urls,
            temporal=temp,
            location=loc,
            media_info=mi,
            ocr_text=ocr_text,
            scene=scene,
            objects=objects,
            place_candidates=places,
            summary=summary,
            tags=tags,
            tag_details=tag_details,
            artistic_notes=artistic_notes,
            extraction_notes=extraction_notes,
            analysis=analysis,
            location_meta=location_meta,
            user_context=user_context,
            series=series,
            extraction_status=extraction_status,
            extraction_run=extraction_run,
        )


@router.post("/{asset_id}/user-context", response_model=UserContextInfo)
async def update_asset_user_context(asset_id: str, body: UpdateUserContextRequest) -> UserContextInfo:
    import uuid as _uuid
    from datetime import datetime, timezone
    from sqlalchemy import select as sa_select
    from models import Asset, Assertion

    try:
        _uuid.UUID(asset_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Asset not found")

    normalized = {
        "user.place": _norm_phrase(body.place),
        "user.gps_coords": _norm_phrase(body.gps_coords),
        "user.comments": _norm_phrase(body.comments),
    }

    with get_session() as session:
        asset = session.get(Asset, asset_id)
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")

        existing = session.scalars(
            sa_select(Assertion).where(
                Assertion.asset_id == asset_id,
                Assertion.is_active == True,  # noqa: E712
                Assertion.predicate.in_(list(normalized.keys())),
            )
        ).all()
        for row in existing:
            row.is_active = False

        now = datetime.now(timezone.utc)
        for predicate, value in normalized.items():
            if not value:
                continue
            session.add(
                Assertion(
                    asset_id=asset_id,
                    predicate=predicate,
                    value=value,
                    confidence=1.0,
                    source="user",
                    extraction_run_id=None,
                    superseded_by=None,
                    is_active=True,
                    user_verified=True,
                    created_at=now,
                )
            )
        session.commit()

    return UserContextInfo(
        place=normalized["user.place"],
        gps_coords=normalized["user.gps_coords"],
        comments=normalized["user.comments"],
    )


@router.get("/review/queues", response_model=ReviewQueueResponse)
async def get_review_queues(limit: int = Query(12, ge=1, le=24)) -> ReviewQueueResponse:
    from repositories.assets import list_assets as db_list_assets

    queue_specs = [
        ("needs-extraction", "Needs Extraction", "Assets that still have no successful AI pass."),
        ("timestamp-conflict", "Timestamp Conflict", "Assets where date sources disagree."),
        ("low-confidence", "Low Confidence", "Assets whose current scene extraction confidence is weak."),
        ("location-unverified", "GPS But No Place", "Assets with coordinates but no inferred place context yet."),
    ]

    queues: list[ReviewQueueItem] = []
    with get_session() as session:
        for name, label, description in queue_specs:
            items, total = db_list_assets(
                session,
                review_bucket=name,
                page=1,
                page_size=limit,
            )
            queues.append(
                ReviewQueueItem(
                    name=name,
                    label=label,
                    description=description,
                    count=total,
                    items=[_asset_to_list_item(asset) for asset in items],
                )
            )
    return ReviewQueueResponse(queues=queues)


@router.get("/{asset_id}", response_model=AssetListItem)
async def get_asset(asset_id: str) -> AssetListItem:
    import uuid as _uuid
    from repositories.assets import get_asset_by_id

    try:
        _uuid.UUID(asset_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Asset not found")

    with get_session() as session:
        asset = get_asset_by_id(session, asset_id)
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        return _asset_to_list_item(asset)
