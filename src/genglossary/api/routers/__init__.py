"""API routers."""

from genglossary.api.routers.files import router as files_router
from genglossary.api.routers.health import router as health_router
from genglossary.api.routers.issues import router as issues_router
from genglossary.api.routers.provisional import router as provisional_router
from genglossary.api.routers.refined import router as refined_router
from genglossary.api.routers.terms import router as terms_router

__all__ = [
    "health_router",
    "terms_router",
    "provisional_router",
    "issues_router",
    "refined_router",
    "files_router",
]
