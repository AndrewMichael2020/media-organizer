from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from enum import Enum
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from app.core.db import get_session

router = APIRouter(tags=["jobs"])
logger = logging.getLogger(__name__)
_CANCELLED_JOBS: set[str] = set()


class JobType(str, Enum):
    scan = "scan"
    enrich = "enrich"
    extract = "extract"
    reprocess = "reprocess"


class JobStatus(str, Enum):
    queued = "queued"
    running = "running"
    done = "done"
    failed = "failed"
    cancelled = "cancelled"


class JobOut(BaseModel):
    id: str
    type: str
    status: str
    started_at: datetime
    finished_at: datetime | None = None
    message: str | None = None
    progress_current: int = 0
    progress_total: int = 0


class StartJobRequest(BaseModel):
    type: JobType
    source_root: str | None = None
    asset_ids: list[str] | None = None
    model_provider: str | None = None
    model_name: str | None = None


def _job_to_out(job) -> JobOut:
    return JobOut(
        id=job.id,
        type=job.job_type,
        status=job.status,
        started_at=job.started_at,
        finished_at=job.finished_at,
        message=job.message,
        progress_current=job.progress_current,
        progress_total=job.progress_total,
    )


@router.get("", response_model=list[JobOut])
async def list_jobs() -> list[JobOut]:
    from sqlalchemy import select
    from models import JobRun

    with get_session() as session:
        jobs = session.scalars(
            select(JobRun).order_by(JobRun.started_at.desc()).limit(50)
        ).all()
        return [_job_to_out(j) for j in jobs]


@router.get("/{job_id}", response_model=JobOut)
async def get_job(job_id: str) -> JobOut:
    from models import JobRun

    with get_session() as session:
        job = session.get(JobRun, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return _job_to_out(job)


@router.post("/ingest", response_model=JobOut, status_code=202)
async def start_ingest(req: StartJobRequest, background_tasks: BackgroundTasks) -> JobOut:
    from models import JobRun

    with get_session() as session:
        queued_message = f"Queued {req.type.value}"
        if req.type == JobType.extract and req.model_provider and req.model_name:
            queued_message = f"Queued {req.type.value} with {req.model_provider}/{req.model_name}"
        job = JobRun(
            job_type=req.type.value,
            status="queued",
            source_root=req.source_root,
            message=queued_message,
        )
        session.add(job)
        session.flush()
        job_id = job.id

    background_tasks.add_task(_run_job, job_id, req)
    with get_session() as session:
        job = session.get(JobRun, job_id)
        return _job_to_out(job)


@router.post("/{job_id}/stop", response_model=JobOut)
async def stop_job(job_id: str) -> JobOut:
    from models import JobRun

    with get_session() as session:
        job = session.get(JobRun, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        if job.status not in ("queued", "running"):
            return _job_to_out(job)
        _CANCELLED_JOBS.add(job_id)
        job.message = "Stop requested..."
        return _job_to_out(job)


class CostStats(BaseModel):
    total_runs: int
    total_tokens_in: int
    total_tokens_out: int
    total_cost_usd: float
    avg_cost_per_run_usd: float


@router.get("/extraction/cost-stats", response_model=CostStats)
async def get_cost_stats() -> CostStats:
    """Aggregate token usage and cost across all successful extraction runs."""
    from sqlalchemy import select, func
    from models import ExtractionRun

    with get_session() as session:
        row = session.execute(
            select(
                func.count(ExtractionRun.id).label("runs"),
                func.coalesce(func.sum(ExtractionRun.tokens_in), 0).label("tok_in"),
                func.coalesce(func.sum(ExtractionRun.tokens_out), 0).label("tok_out"),
                func.coalesce(func.sum(ExtractionRun.cost_usd), 0.0).label("cost"),
            ).where(ExtractionRun.status == "done")
        ).one()
        runs = row.runs or 0
        return CostStats(
            total_runs=runs,
            total_tokens_in=row.tok_in,
            total_tokens_out=row.tok_out,
            total_cost_usd=round(row.cost, 6),
            avg_cost_per_run_usd=round(row.cost / runs, 6) if runs else 0.0,
        )


async def _run_job(job_id: str, req: StartJobRequest) -> None:
    """Background task: run scan or enrich job and update job_run record."""
    import sys
    from pathlib import Path
    _repo = Path(__file__).parents[4]  # …/media-organizer
    sys.path.insert(0, str(_repo / "packages" / "storage"))
    sys.path.insert(0, str(_repo / "packages" / "media"))

    from models import JobRun
    from datetime import timezone
    from sqlalchemy import select, func
    from models import Asset

    def _cancelled() -> bool:
        return job_id in _CANCELLED_JOBS

    def _update(status: str, message: str = ""):
        with get_session() as s:
            j = s.get(JobRun, job_id)
            if j:
                j.status = status
                j.message = message
                if status in ("done", "failed"):
                    j.finished_at = datetime.now(timezone.utc)
                if status == "cancelled":
                    j.finished_at = datetime.now(timezone.utc)

    def _count_assets_in_scope(scope: str | None) -> int:
        with get_session() as s:
            q = select(func.count(Asset.id)).where(Asset.is_missing == False)  # noqa: E712
            if scope:
                q = q.where(
                    (Asset.canonical_path == scope) | (Asset.canonical_path.like(f"{scope}/%"))
                )
            return s.scalar(q) or 0

    async def _ensure_assets_for_scope(scope: str | None) -> None:
        if not scope:
            return
        if _count_assets_in_scope(scope) > 0:
            return
        from scanner import scan_source_root
        _update("running", f"No indexed assets found in {scope}. Scanning folder first…")
        result = await asyncio.to_thread(scan_source_root, scope)
        _update("running", f"Scan done — {result.new} new, {result.updated} updated, {result.found} found. Continuing…")

    running_message = f"Starting {req.type.value}…"
    if req.type == JobType.extract and req.model_provider and req.model_name:
        running_message = f"Starting {req.type.value} with {req.model_provider}/{req.model_name}…"
    _update("running", running_message)
    try:
        scoped = str(Path(req.source_root).expanduser().resolve()) if req.source_root else None
        if req.type == JobType.scan:
            from scanner import scan_source_root
            result = await asyncio.to_thread(scan_source_root, req.source_root or "")
            _update("done", f"Scan done — {result.new} new, {result.updated} updated, {result.found} found")
        elif req.type == JobType.enrich:
            from enrichment import enrich_all_pending
            await _ensure_assets_for_scope(scoped)
            done, errors, cancelled = await asyncio.to_thread(enrich_all_pending, 200, scoped, _cancelled)
            _update("cancelled" if cancelled else "done", f"Enriched {done} assets ({errors} errors)")
        elif req.type == JobType.extract:
            sys.path.insert(0, str(_repo / "packages" / "vision"))
            sys.path.insert(0, str(_repo / "packages" / "models"))
            from image_extractor import extract_all_pending
            from app.core.config import settings
            await _ensure_assets_for_scope(scoped)
            stats = await asyncio.to_thread(
                extract_all_pending,
                req.model_provider or settings.model_provider,
                req.model_name or settings.model_name,
                50,
                settings.worker_image_analysis_max_px,
                settings.worker_ai_max_output_tokens,
                scoped,
                _cancelled,
            )
            detail = ""
            if stats.get("failure_examples"):
                detail = " | " + " ; ".join(stats["failure_examples"])
            _update(
                "cancelled" if stats.get("cancelled") else "done",
                f"Extracted {stats['processed']} assets ({stats['failed']} failed, {stats['skipped']} skipped){detail}"
            )
        elif req.type == JobType.reprocess:
            from thumbnails import generate_all_pending
            from app.core.config import settings
            await _ensure_assets_for_scope(scoped)
            stats = await asyncio.to_thread(generate_all_pending, settings.derivative_cache_root, scoped, _cancelled)
            _update(
                "cancelled" if stats.get("cancelled") else "done",
                f"Thumbnails done — {stats['processed']} generated, {stats['skipped']} skipped, {stats['failed']} failed"
            )
        else:
            _update("done", f"{req.type.value} not implemented")
    except Exception as exc:
        logger.exception("Job %s failed", job_id)
        _update("failed", str(exc))
    finally:
        _CANCELLED_JOBS.discard(job_id)
