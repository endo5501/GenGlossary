"""API routers."""

from genglossary.api.routers.health import router as health_router
from genglossary.api.routers.terms import router as terms_router

__all__ = ["health_router", "terms_router"]
