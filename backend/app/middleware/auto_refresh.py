"""
Automatic token refresh middleware for seamless authentication
"""

import logging
from typing import Callable, Optional, Tuple

from fastapi import Request, Response  # type: ignore
from starlette.middleware.base import BaseHTTPMiddleware  # type: ignore

from app.core.jwt import auto_refresh_tokens, is_token_expiring_soon

logger = logging.getLogger(__name__)


class AutoRefreshMiddleware(BaseHTTPMiddleware):
    """Middleware for automatically refreshing tokens before they expire"""

    def __init__(self, app, threshold_minutes: int = 5):
        super().__init__(app)
        self.threshold_minutes = threshold_minutes

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip auth endpoints to avoid infinite loops
        if request.url.path.startswith("/auth/"):
            return await call_next(request)

        # Extract tokens from request
        access_token = self._extract_access_token(request)
        refresh_token = self._extract_refresh_token(request)

        # Check if we need to refresh tokens
        if access_token and refresh_token:
            if is_token_expiring_soon(access_token, self.threshold_minutes):
                logger.debug("Access token expiring soon, attempting auto-refresh")

                # Attempt automatic refresh
                new_access, new_refresh, error = auto_refresh_tokens(access_token, refresh_token)

                if new_access and new_refresh and not error:
                    # Store new tokens in request state for later use
                    request.state.new_access_token = new_access
                    request.state.new_refresh_token = new_refresh
                    logger.info("Tokens automatically refreshed")
                else:
                    logger.warning(f"Auto-refresh failed: {error}")

        # Process the request
        response = await call_next(request)

        # Add new tokens to response headers if available
        if hasattr(request.state, "new_access_token"):
            response.headers["X-New-Access-Token"] = request.state.new_access_token
            logger.debug("Added new access token to response headers")

        if hasattr(request.state, "new_refresh_token"):
            response.headers["X-New-Refresh-Token"] = request.state.new_refresh_token
            logger.debug("Added new refresh token to response headers")

        return response

    def _extract_access_token(self, request: Request) -> Optional[str]:
        """Extract access token from Authorization header"""
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header.split(" ")[1]
        return None

    def _extract_refresh_token(self, request: Request) -> Optional[str]:
        """Extract refresh token from cookies or headers"""
        # Try cookies first (more secure for web apps)
        refresh_token = request.cookies.get("refresh_token")
        if refresh_token:
            return refresh_token

        # Fallback to custom header
        return request.headers.get("X-Refresh-Token")


# Convenience function for manual token refresh
async def manual_refresh_tokens(
    access_token: str, refresh_token: str
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Manually refresh tokens - useful for client-side token management

    Returns:
        tuple: (new_access_token, new_refresh_token, error_message)
    """
    from app.core.jwt import auto_refresh_tokens

    return auto_refresh_tokens(access_token, refresh_token)
