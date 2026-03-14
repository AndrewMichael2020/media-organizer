from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from enum import Enum

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from app.core.db import get_session

router = APIRouter(tags=["jobs"])
logger = logging.getLogger(__name__)


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
        job = JobRun(
            job_type=req.type.value,
            status="queued",
            source_root=req.source_root,
            message=f"Queued {req.type.value}",
        )
        session.add(job)
        session.flush()
        job_id = job.id

    background_tasks.add_task(_run_job, job_id, req)
    with get_session() as session:
        job = session.get(JobRun, job_id)
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

    def _update(status: str, message: str = ""):
        with get_session() as s:
            j = s.get(JobRun, job_id)
            if j:
                j.status = status
                j.message = message
                if status in ("done", "failed"):
                    j.finished_at = datetime.now(timezone.utc)

    _update("running", f"Starting {req.type.value}…")
    try:
        if req.type == JobType.scan:
            from scanner import scan_source_root
            result = await asyncio.to_thread(scan_source_root, req.source_root or "")
            _update("done", f"Scan done — {result.new} new, {result.updated} updated, {result.found} found")
        elif req.type == JobType.enrich:
            from enrichment import enrich_all_pending
            done, errors = await asyncio.to_thread(enrich_all_pending)
            _update("done", f"Enriched {done} assets ({errors} errors)")
        elif req.type == JobType.extract:
            sys.path.insert(0, str(_repo / "packages" / "vision"))
            sys.path.insert(0, str(_repo / "packages" / "models"))
            from image_extractor import extract_all_pending
            from app.core.config import settings
            stats = await asyncio.to_thread(
                extract_all_pending,
                settings.model_provider,
                settings.model_name,
            )
            _update("done", f"Extracted {stats['processed']} assets ({stats['failed']} failed, {stats['skipped']} skipped)")
        elif req.type == JobType.reprocess:
            from thumbnails import generate_all_pending
            from app.core.config import settings
            stats = await asyncio.to_thread(generate_all_pending, settings.derivative_cache_root)
            _update("done", f"Thumbnails done — {stats['processed']} generated, {stats['skipped']} skipped, {stats['failed']} failed")
        else:
            _update("done", f"{req.type.value} not implemented")
    except Exception as exc:
        logger.exception("Job %s failed", job_id)
        _update("failed", str(exc))
