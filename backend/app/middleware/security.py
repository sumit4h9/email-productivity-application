"""
Security headers middleware for enhanced application security
"""

import logging
from typing import Callable

from fastapi import Request  # type: ignore
from starlette.middleware.base import BaseHTTPMiddleware  # type: ignore

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses
    """

    def __init__(self, app):
        super().__init__(app)
        self.security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self'; "
                "connect-src 'self'; "
                "frame-ancestors 'none';"
            ),
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        }

    async def dispatch(self, request: Request, call_next: Callable):
        """Add security headers to response"""
        try:
            response = await call_next(request)

            # Add security headers
            for header, value in self.security_headers.items():
                response.headers[header] = value

            # Remove server header for security
            if "server" in response.headers:
                del response.headers["server"]

            return response

        except Exception as e:
            logger.error(f"Security middleware error: {e}")
            # Let the request continue even if security headers fail
            return await call_next(request)
