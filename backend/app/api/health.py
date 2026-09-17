"""Health-check endpoint."""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Response returned by the API health check."""

    status: str


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Report whether the API process is available."""
    return HealthResponse(status="ok")
