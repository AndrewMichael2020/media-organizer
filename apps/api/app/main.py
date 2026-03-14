from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import health, assets, jobs, config

app = FastAPI(
    title="Forensic Media Organizer API",
    version="0.1.0",
    description="Local-first forensic media catalog API",
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
