"""API routers."""

from genglossary.api.routers.excluded_terms import router as excluded_terms_router
from genglossary.api.routers.files import router as files_router
from genglossary.api.routers.health import router as health_router
from genglossary.api.routers.issues import router as issues_router
from genglossary.api.routers.ollama import router as ollama_router
from genglossary.api.routers.projects import router as projects_router
from genglossary.api.routers.provisional import router as provisional_router
from genglossary.api.routers.refined import router as refined_router
from genglossary.api.routers.runs import router as runs_router
from genglossary.api.routers.terms import router as terms_router

__all__ = [
    "excluded_terms_router",
    "files_router",
    "health_router",
    "issues_router",
    "ollama_router",
    "projects_router",
    "provisional_router",
    "refined_router",
    "runs_router",
    "terms_router",
]
