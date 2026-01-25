"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from genglossary import __version__
from genglossary.api.middleware import (
    RequestIDMiddleware,
    StructuredLoggingMiddleware,
)
from genglossary.api.routers import health_router


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

    # CORS middleware - allow localhost:3000, 5173 (Vite default), 127.0.0.1:3000, 5173
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
    )

    # Request ID middleware
    app.add_middleware(RequestIDMiddleware)

    # Structured logging middleware
    app.add_middleware(StructuredLoggingMiddleware)

    # Include routers
    app.include_router(health_router)

    return app
