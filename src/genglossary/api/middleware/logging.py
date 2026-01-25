"""Structured logging middleware."""

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log requests and responses in structured format."""

    async def dispatch(self, request: Request, call_next) -> Response:
        """Log request and response details.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware in chain

        Returns:
            Response: HTTP response
        """
        start_time = time.time()

        # Get request ID if available
        request_id = getattr(request.state, "request_id", None)

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time

        # Log structured data
        logger.info(
            "HTTP request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration": duration,
            },
        )

        return response
