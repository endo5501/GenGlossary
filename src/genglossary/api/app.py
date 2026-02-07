"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from genglossary import __version__
from genglossary.api.middleware import (
    RequestIDMiddleware,
    StructuredLoggingMiddleware,
)
from genglossary.api.routers import (
    excluded_terms_router,
    files_router,
    health_router,
    issues_router,
    ollama_router,
    projects_router,
    provisional_router,
    refined_router,
    required_terms_router,
    runs_router,
    terms_router,
)


def create_app() -> FastAPI:
    """Create and configure FastAPI application.

    Returns:
        FastAPI: Configured FastAPI application instance
    """
    app = FastAPI(
        title="GenGlossary API",
        description="API for GenGlossary - AI-powered glossary generation tool",
        version=__version__,
    )

    # Middleware stack (applied in reverse order: last added = first executed)
    # Order: CORS -> RequestID -> StructuredLogging -> routes

    # Structured logging middleware (last executed, can access request_id)
    app.add_middleware(StructuredLoggingMiddleware)

    # Request ID middleware (sets request_id before logging)
    app.add_middleware(RequestIDMiddleware)

    # CORS middleware (first executed, expose X-Request-ID for JS)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    # Include routers
    app.include_router(health_router)
    app.include_router(projects_router)
    app.include_router(terms_router)
    app.include_router(excluded_terms_router)
    app.include_router(required_terms_router)
    app.include_router(provisional_router)
    app.include_router(issues_router)
    app.include_router(refined_router)
    app.include_router(files_router)
    app.include_router(runs_router)
    app.include_router(ollama_router, prefix="/api")

    return app
