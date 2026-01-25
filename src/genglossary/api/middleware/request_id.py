"""Request ID middleware."""

import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add X-Request-ID header to all responses."""

    async def dispatch(self, request: Request, call_next) -> Response:
        """Add X-Request-ID header to response.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware in chain

        Returns:
            Response: HTTP response with X-Request-ID header
        """
        # Generate UUID for this request
        request_id = str(uuid.uuid4())

        # Store in request.state for logging
        request.state.request_id = request_id

        # Process request
        response = await call_next(request)

        # Add header to response
        response.headers["X-Request-ID"] = request_id

        return response
