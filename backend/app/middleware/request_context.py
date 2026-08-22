import time
import uuid
from typing import Callable

from fastapi import Request, Response  # type: ignore
from starlette.middleware.base import BaseHTTPMiddleware  # type: ignore


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Adds a per-request correlation ID and timing to request state and response headers."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = uuid.uuid4().hex
        request.state.request_id = request_id
        start = time.time()

        response = await call_next(request)

        duration_ms = int((time.time() - start) * 1000)
        # Expose correlation id and basic timing
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = str(duration_ms)
        return response
