from __future__ import annotations

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
    has_ocr: bool = False
    has_gps: bool = False
    is_duplicate: bool = False
    thumbnail_url: str | None = None
    width: int | None = None
    height: int | None = None


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
    has_conflict: bool = False

class SceneInfo(BaseModel):
    setting: str | None = None
    time_of_day: str | None = None
    weather: str | None = None
    description: str | None = None

class PlaceInfo(BaseModel):
    name: str | None = None
    country: str | None = None
    region: str | None = None
    place_type: str | None = None
    confidence: float | None = None

class ObjectInfo(BaseModel):
    label: str
    confidence: float | None = None
    count: int | None = None

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
    extraction_status: str | None = None


@router.get("", response_model=AssetListResponse)
async def list_assets(
    q: str | None = Query(None, description="Full-text search query"),
    page: int = Query(1, ge=1),
    page_size: int = Query(48, ge=1, le=200),
    asset_type: str | None = Query(None, alias="type"),
) -> AssetListResponse:
    from repositories.assets import list_assets as db_list_assets

    with get_session() as session:
        assets, total = db_list_assets(
            session,
            media_type=asset_type,
            search=q,
            page=page,
            page_size=page_size,
        )
        items = [
            AssetListItem(
                id=a.id,
                filename=a.filename,
                type=a.media_type,
                date=a.temporal.best_timestamp.date().isoformat() if a.temporal and a.temporal.best_timestamp else None,
                has_gps=a.location is not None,
                has_ocr=False,
                width=a.media_info.width if a.media_info else None,
                height=a.media_info.height if a.media_info else None,
                thumbnail_url=(
                    f"/api/assets/{a.id}/thumbnail"
                    if a.thumbnails or a.keyframes else None
                ),
            )
            for a in assets
        ]
    return AssetListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{asset_id}/thumbnail")
async def get_thumbnail(asset_id: str, size: str = "small"):
    """Serve the thumbnail JPEG for an asset.

    ?size=small  → 400px (default, for gallery)
    ?size=large  → 1200px (for detail view / AI analysis)
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
                # Prefer largest available
                thumb = thumbs[-1]
            else:
                # Prefer smallest (400px) for gallery
                thumb = thumbs[0]
            if _Path(thumb.path).exists():
                return FileResponse(thumb.path, media_type="image/jpeg")

        # Fall back to first keyframe
        if asset.keyframes:
            kf = sorted(asset.keyframes, key=lambda k: k.sequence_index)[0]
            from pathlib import Path as _Path
            if _Path(kf.path).exists():
                return FileResponse(kf.path, media_type="image/jpeg")

    raise HTTPException(status_code=404, detail="No thumbnail generated yet")


@router.get("/{asset_id}/detail", response_model=AssetDetail)
async def get_asset_detail(asset_id: str) -> AssetDetail:
    """Full detail including enrichment, AI extraction results."""
    import uuid as _uuid
    from models import Asset, OcrDocument, SceneSummary, ObjectDetection, PlaceCandidate, ExtractionRun

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
                best_timestamp=t.best_timestamp.isoformat() if t.best_timestamp else None,
                source=t.best_timestamp_source,
                has_conflict=t.has_conflict or False,
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
            mi = MediaInfo(
                width=m.width, height=m.height,
                duration_seconds=m.duration_seconds,
                codec=m.video_codec,
                camera_make=m.make,
                camera_model=m.model,
                lens_model=exif.get("LensModel") or exif.get("Lens"),
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
        extraction_status = None

        if run:
            extraction_status = run.status
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
                )

            # Objects
            objs = session.scalars(
                sa_select(ObjectDetection).where(ObjectDetection.extraction_run_id == run.id)
            ).all()
            objects = [ObjectInfo(label=o.label, confidence=o.confidence, count=o.attributes.get("count") if o.attributes else None) for o in objs]

            # Places
            pcs = session.scalars(
                sa_select(PlaceCandidate).where(PlaceCandidate.extraction_run_id == run.id)
            ).all()
            places = [PlaceInfo(name=p.name, country=p.country, region=p.region, place_type=p.place_type, confidence=p.confidence) for p in pcs]
        else:
            # Check if extraction was attempted but failed
            any_run = session.scalar(
                sa_select(ExtractionRun)
                .where(ExtractionRun.asset_id == asset_id)
                .order_by(ExtractionRun.started_at.desc())
            )
            if any_run:
                extraction_status = any_run.status

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
            extraction_status=extraction_status,
        )


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
        return AssetListItem(
            id=asset.id,
            filename=asset.filename,
            type=asset.media_type,
            date=asset.temporal.best_timestamp.date().isoformat() if asset.temporal and asset.temporal.best_timestamp else None,
            has_gps=asset.location is not None,
            width=asset.media_info.width if asset.media_info else None,
            height=asset.media_info.height if asset.media_info else None,
        )
