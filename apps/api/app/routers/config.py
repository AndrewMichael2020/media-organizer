"""
Config management endpoints — source roots, runtime settings.
"""
from __future__ import annotations

import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

if TYPE_CHECKING:
    pass

router = APIRouter(tags=["config"])


class SourceRootIn(BaseModel):
    path: str


class SourceRootInfo(BaseModel):
    path: str
    exists: bool
    readable: bool
    file_count_estimate: int | None = None


class ConfigSnapshot(BaseModel):
    source_roots: list[SourceRootInfo]
    derivative_cache_root: str
    model_provider: str
    model_name: str
    deepinfra_base_url: str
    lmstudio_base_url: str
    default_model_profile_key: str
    model_profiles: list["ModelProfile"]
    api_version: str = "0.1.0"


class ModelProfile(BaseModel):
    key: str
    label: str
    provider: str
    model_name: str
    kind: str
    execution_mode: str = "standard"
    image_max_px: int | None = None


class PurgeMetadataRequest(BaseModel):
    confirm_text: str


class PurgeMetadataResponse(BaseModel):
    status: str
    tables_reset: bool
    cache_root: str
    cache_cleared: bool
    debug_cleared: bool


@router.get("", response_model=ConfigSnapshot)
async def get_config() -> ConfigSnapshot:
    from app.core.config import settings

    roots = []
    for root in settings.source_roots:
        p = Path(root).expanduser()
        exists = p.exists()
        readable = exists and os.access(p, os.R_OK)
        estimate = None
        if readable:
            try:
                # Cheap estimate: count top-level entries only
                estimate = sum(1 for _ in p.iterdir())
            except PermissionError:
                pass
        roots.append(SourceRootInfo(path=str(p), exists=exists, readable=readable, file_count_estimate=estimate))

    return ConfigSnapshot(
        source_roots=roots,
        derivative_cache_root=settings.derivative_cache_root,
        model_provider=settings.model_provider,
        model_name=settings.model_name,
        deepinfra_base_url=settings.deepinfra_base_url,
        lmstudio_base_url=settings.lmstudio_base_url,
        default_model_profile_key="gemini-25-flash-lite-batch",
        model_profiles=[
            ModelProfile(
                key="gemini-25-flash-lite-batch",
                label="Gemini · gemini-2.5-flash-lite + Batch",
                provider="gemini",
                model_name="gemini-2.5-flash-lite",
                kind="cloud",
                execution_mode="batch",
                image_max_px=768,
            ),
            ModelProfile(
                key="gemini-25-flash-lite",
                label="Gemini · gemini-2.5-flash-lite",
                provider="gemini",
                model_name="gemini-2.5-flash-lite",
                kind="cloud",
                execution_mode="standard",
                image_max_px=1200,
            ),
            ModelProfile(
                key="gemini-default",
                label=f"Gemini · {settings.model_name}",
                provider=settings.model_provider,
                model_name=settings.model_name,
                kind="cloud",
                execution_mode="standard",
                image_max_px=1200,
            ),
            ModelProfile(
                key="deepinfra-llama32-11b",
                label=f"DeepInfra · {settings.deepinfra_default_model}",
                provider="deepinfra",
                model_name=settings.deepinfra_default_model,
                kind="cloud",
                execution_mode="standard",
                image_max_px=1200,
            ),
            ModelProfile(
                key="deepinfra-llama32-11b-batch",
                label=f"DeepInfra · {settings.deepinfra_default_model} (app batch)",
                provider="deepinfra",
                model_name=settings.deepinfra_default_model,
                kind="cloud",
                execution_mode="batch",
                image_max_px=768,
            ),
            ModelProfile(
                key="lmstudio-gemma-27b",
                label=f"LM Studio · {settings.lmstudio_default_model}",
                provider="lmstudio",
                model_name=settings.lmstudio_default_model,
                kind="local",
                execution_mode="standard",
                image_max_px=1200,
            ),
            ModelProfile(
                key="lmstudio-gemma-3n-e4b",
                label="LM Studio · google/gemma-3n-e4b",
                provider="lmstudio",
                model_name="google/gemma-3n-e4b",
                kind="local",
                execution_mode="standard",
                image_max_px=1200,
            ),
        ],
    )


@router.post("/source-roots/validate", response_model=SourceRootInfo)
async def validate_source_root(body: SourceRootIn) -> SourceRootInfo:
    """Check whether a path exists and is readable on this machine."""
    p = Path(body.path).expanduser().resolve()
    exists = p.exists() and p.is_dir()
    readable = exists and os.access(p, os.R_OK)
    estimate = None
    if readable:
        try:
            estimate = sum(1 for _ in p.iterdir())
        except PermissionError:
            pass
    return SourceRootInfo(path=str(p), exists=exists, readable=readable, file_count_estimate=estimate)


@router.post("/pick-folder", response_model=SourceRootInfo)
async def pick_folder_native() -> SourceRootInfo:
    """
    Open the OS-native folder picker dialog and return the chosen path.
    macOS only (uses osascript). Returns 422 on other platforms or if user cancels.
    """
    if platform.system() != "Darwin":
        raise HTTPException(status_code=422, detail="Native folder picker is only supported on macOS")

    script = 'POSIX path of (choose folder with prompt "Select a media folder to scan")'
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=120,
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Folder picker timed out")

    if result.returncode != 0:
        # User cancelled → osascript exits with code 1
        raise HTTPException(status_code=400, detail="No folder selected")

    chosen = result.stdout.strip()
    if not chosen:
        raise HTTPException(status_code=400, detail="No folder selected")

    p = Path(chosen).resolve()
    exists = p.exists() and p.is_dir()
    readable = exists and os.access(p, os.R_OK)
    estimate = None
    if readable:
        try:
            estimate = sum(1 for _ in p.iterdir())
        except PermissionError:
            pass
    return SourceRootInfo(path=str(p), exists=exists, readable=readable, file_count_estimate=estimate)

@router.post("/source-roots/scan", status_code=202)
async def scan_source_root(body: SourceRootIn, background_tasks: BackgroundTasks) -> dict:
    """Validate path and kick a scan job."""
    from app.core.db import get_session

    p = Path(body.path).expanduser().resolve()
    if not p.exists() or not p.is_dir():
        raise HTTPException(status_code=422, detail=f"Path does not exist or is not a directory: {p}")
    if not os.access(p, os.R_OK):
        raise HTTPException(status_code=422, detail=f"Path is not readable: {p}")

    from models import JobRun
    from datetime import datetime, timezone

    with get_session() as session:
        job = JobRun(
            job_type="scan",
            status="queued",
            source_root=str(p),
            message=f"Scan queued for {p}",
        )
        session.add(job)
        session.flush()
        job_id = job.id

    async def _run():
        import sys, asyncio
        _repo = Path(__file__).parents[4]  # …/media-organizer
        sys.path.insert(0, str(_repo / "packages" / "storage"))
        from scanner import scan_source_root as _scan
        from models import JobRun
        from datetime import timezone

        def _update(status: str, msg: str):
            with get_session() as s:
                j = s.get(JobRun, job_id)
                if j:
                    j.status = status
                    j.message = msg
                    if status in ("done", "failed"):
                        j.finished_at = datetime.now(timezone.utc)

        _update("running", f"Scanning {p}…")
        try:
            result = await asyncio.to_thread(_scan, str(p))
            _update("done", f"Done — {result.new} new, {result.updated} updated, {result.found} found")
        except Exception as exc:
            _update("failed", str(exc))

    background_tasks.add_task(_run)
    return {"job_id": job_id, "status": "queued", "source_root": str(p)}


@router.post("/purge-metadata", response_model=PurgeMetadataResponse)
async def purge_metadata(body: PurgeMetadataRequest) -> PurgeMetadataResponse:
    from app.core.config import settings
    from app.core.db import get_engine
    from models import Base

    expected = "PURGE ALL METADATA"
    if body.confirm_text.strip() != expected:
        raise HTTPException(status_code=422, detail=f'Type exactly "{expected}" to continue')

    engine = get_engine()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    cache_root = Path(settings.derivative_cache_root).expanduser()
    cache_cleared = False
    if cache_root.exists():
        shutil.rmtree(cache_root, ignore_errors=True)
        cache_cleared = True
    cache_root.mkdir(parents=True, exist_ok=True)

    repo_root = Path(__file__).parents[4]
    debug_root = repo_root / "var" / "ai_debug"
    debug_cleared = False
    if debug_root.exists():
        shutil.rmtree(debug_root, ignore_errors=True)
        debug_cleared = True
    debug_root.mkdir(parents=True, exist_ok=True)

    return PurgeMetadataResponse(
        status="purged",
        tables_reset=True,
        cache_root=str(cache_root),
        cache_cleared=cache_cleared,
        debug_cleared=debug_cleared,
    )
