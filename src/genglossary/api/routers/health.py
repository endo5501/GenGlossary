"""Health check and version endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter

from genglossary import __version__
from genglossary.api.schemas import HealthResponse, VersionResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint.

    Returns:
        HealthResponse: Health status and timestamp
    """
    return HealthResponse(
        status="ok",
        timestamp=datetime.now(timezone.utc),
    )


@router.get("/version", response_model=VersionResponse)
async def version_info() -> VersionResponse:
    """Version information endpoint.

    Returns:
        VersionResponse: Application name and version
    """
    return VersionResponse(
        name="genglossary",
        version=__version__,
    )
