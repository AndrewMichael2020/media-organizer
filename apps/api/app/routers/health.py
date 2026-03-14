from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    db: str
    version: str


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    # TODO: check real DB connection once DB is wired
    return HealthResponse(status="ok", db="ok", version="0.1.0")
