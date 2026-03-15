from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.db import get_session
from app.routers import health, assets, jobs, config


@asynccontextmanager
async def lifespan(_app: FastAPI):
    from datetime import datetime, timezone
    from sqlalchemy import update
    from models import JobRun

    with get_session() as session:
        session.execute(
            update(JobRun)
            .where(JobRun.status.in_(["queued", "running"]))
            .values(
                status="cancelled",
                finished_at=datetime.now(timezone.utc),
                message="Cancelled because the API server restarted before the job finished.",
            )
        )
    yield


app = FastAPI(
    title="Forensic Media Organizer API",
    version="0.1.0",
    description="Local-first forensic media catalog API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(assets.router, prefix="/assets")
app.include_router(jobs.router, prefix="/jobs")
app.include_router(config.router, prefix="/config")
