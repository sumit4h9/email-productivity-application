"""
Token utilities for client-side token management and automatic refresh
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, Optional

import requests  # type: ignore

logger = logging.getLogger(__name__)


class TokenManager:
    """Client-side token manager with automatic refresh capabilities"""

    def __init__(
        self,
        api_base_url: str,
        access_token: str,
        refresh_token: str,
        refresh_threshold_minutes: int = 5,
        auto_refresh: bool = True,
    ):
        self.api_base_url = api_base_url.rstrip("/")
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.refresh_threshold_minutes = refresh_threshold_minutes
        self.auto_refresh = auto_refresh
        self._refresh_lock = asyncio.Lock()
        self._last_refresh = 0
        self._refresh_cooldown = 30  # seconds between refresh attempts

    def is_access_token_expiring_soon(self, threshold_minutes: Optional[int] = None) -> bool:
        """Check if access token is expiring within the specified threshold"""
        if threshold_minutes is None:
            threshold_minutes = self.refresh_threshold_minutes

        try:
            # Decode JWT payload (second part of token)
            import jwt  # type: ignore

            payload = jwt.decode(self.access_token, options={"verify_signature": False})

            exp_timestamp = payload.get("exp")
            if not exp_timestamp:
                return True  # Assume expired if no expiry claim

            # Check if expiring within threshold
            now = time.time()
            return (exp_timestamp - now) <= (threshold_minutes * 60)

        except Exception as e:
            logger.warning(f"Error checking token expiry: {e}")
            return True  # Assume expired on error

    def get_token_expiry_time(self) -> Optional[datetime]:
        """Get the expiry time of the access token"""
        try:
            import jwt  # type: ignore

            payload = jwt.decode(self.access_token, options={"verify_signature": False})

            exp_timestamp = payload.get("exp")
            if not exp_timestamp:
                return None

            return datetime.fromtimestamp(exp_timestamp)

        except Exception as e:
            logger.warning(f"Error getting token expiry time: {e}")
            return None

    def get_auth_headers(self) -> Dict[str, str]:
        """Get headers for authenticated requests"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "X-Refresh-Token": self.refresh_token,
        }

    async def refresh_tokens_async(self) -> bool:
        """Refresh tokens asynchronously"""
        async with self._refresh_lock:
            # Check cooldown to prevent rapid refresh attempts
            if time.time() - self._last_refresh < self._refresh_cooldown:
                logger.debug("Refresh cooldown active, skipping refresh")
                return False

            try:
                # Make refresh request
                response = await self._make_refresh_request_async()

                if response and response.status_code == 200:
                    data = response.json()
                    self.access_token = data["access_token"]
                    self.refresh_token = data["refresh_token"]
                    self._last_refresh = time.time()
                    logger.info("Tokens refreshed successfully")
                    return True
                else:
                    logger.warning(
                        f"Token refresh failed: {response.status_code if response else 'No response'}"
                    )
                    return False

            except Exception as e:
                logger.error(f"Token refresh error: {e}")
                return False

    def refresh_tokens_sync(self) -> bool:
        """Refresh tokens synchronously"""
        try:
            # Check cooldown
            if time.time() - self._last_refresh < self._refresh_cooldown:
                logger.debug("Refresh cooldown active, skipping refresh")
                return False

            # Make refresh request
            response = self._make_refresh_request_sync()

            if response and response.status_code == 200:
                data = response.json()
                self.access_token = data["access_token"]
                self.refresh_token = data["refresh_token"]
                self._last_refresh = time.time()
                logger.info("Tokens refreshed successfully")
                return True
            else:
                logger.warning(
                    f"Token refresh failed: {response.status_code if response else 'No response'}"
                )
                return False

        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return False

    async def _make_refresh_request_async(self):
        """Make async refresh request"""
        try:
            import httpx  # type: ignore

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base_url}/auth/refresh",
                    json={"refresh_token": self.refresh_token},
                    headers={"Content-Type": "application/json"},
                )
                return response
        except ImportError:
            logger.warning("httpx not available, falling back to sync request")
            return self._make_refresh_request_sync()

    def _make_refresh_request_sync(self):
        """Make sync refresh request"""
        try:
            response = requests.post(
                f"{self.api_base_url}/auth/refresh",
                json={"refresh_token": self.refresh_token},
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
            return response
        except Exception as e:
            logger.error(f"Sync refresh request failed: {e}")
            return None

    def should_refresh_tokens(self) -> bool:
        """Check if tokens should be refreshed"""
        if not self.auto_refresh:
            return False

        return self.is_access_token_expiring_soon()

    def get_token_info(self) -> Dict[str, any]:
        """Get comprehensive token information"""
        expiry_time = self.get_token_expiry_time()
        time_until_expiry = None

        if expiry_time:
            time_until_expiry = (expiry_time - datetime.now()).total_seconds()

        return {
            "access_token": self.access_token[:20] + "..." if self.access_token else None,
            "refresh_token": self.refresh_token[:20] + "..." if self.refresh_token else None,
            "expiry_time": expiry_time.isoformat() if expiry_time else None,
            "time_until_expiry_seconds": time_until_expiry,
            "needs_refresh": self.should_refresh_tokens(),
            "last_refresh": (
                datetime.fromtimestamp(self._last_refresh).isoformat()
                if self._last_refresh > 0
                else None
            ),
        }


class AutoRefreshTokenManager(TokenManager):
    """Token manager with automatic background refresh"""

    def __init__(
        self,
        api_base_url: str,
        access_token: str,
        refresh_token: str,
        refresh_threshold_minutes: int = 5,
        check_interval: int = 30,
    ):
        super().__init__(api_base_url, access_token, refresh_token, refresh_threshold_minutes)
        self.check_interval = check_interval
        self._refresh_task: Optional[asyncio.Task] = None
        self._running = False

    async def start_auto_refresh(self):
        """Start automatic background refresh"""
        if self._running:
            return

        self._running = True
        self._refresh_task = asyncio.create_task(self._auto_refresh_loop())
        logger.info("Auto-refresh started")

    async def stop_auto_refresh(self):
        """Stop automatic background refresh"""
        self._running = False
        if self._refresh_task:
            self._refresh_task.cancel()
            try:
                await self._refresh_task
            except asyncio.CancelledError:
                pass
        logger.info("Auto-refresh stopped")

    async def _auto_refresh_loop(self):
        """Background loop for automatic token refresh"""
        while self._running:
            try:
                if self.should_refresh_tokens():
                    await self.refresh_tokens_async()

                await asyncio.sleep(self.check_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Auto-refresh loop error: {e}")
                await asyncio.sleep(self.check_interval)


def create_token_manager(
    api_base_url: str,
    access_token: str,
    refresh_token: str,
    auto_refresh: bool = False,
    check_interval: int = 30,
) -> TokenManager:
    """
    Factory function to create appropriate token manager

    Args:
        api_base_url: Base URL of the API
        access_token: Current access token
        refresh_token: Current refresh token
        auto_refresh: Whether to enable automatic background refresh
        check_interval: Interval for background refresh checks (seconds)

    Returns:
        TokenManager or AutoRefreshTokenManager instance
    """
    if auto_refresh:
        return AutoRefreshTokenManager(
            api_base_url=api_base_url,
            access_token=access_token,
            refresh_token=refresh_token,
            check_interval=check_interval,
        )
    else:
        return TokenManager(
            api_base_url=api_base_url, access_token=access_token, refresh_token=refresh_token
        )


# Utility functions for token validation
def validate_token_format(token: str) -> bool:
    """Validate basic JWT token format"""
    if not token or not isinstance(token, str):
        return False

    parts = token.split(".")
    return len(parts) == 3


def extract_token_payload(token: str) -> Optional[Dict]:
    """Extract payload from JWT token without verification"""
    try:
        import jwt  # type: ignore

        payload = jwt.decode(token, options={"verify_signature": False})
        return payload
    except Exception as e:
        logger.warning(f"Failed to extract token payload: {e}")
        return None


def is_token_expired(token: str) -> bool:
    """Check if token is expired"""
    try:
        import jwt  # type: ignore

        payload = jwt.decode(token, options={"verify_signature": False})
        exp_timestamp = payload.get("exp")

        if not exp_timestamp:
            return True

        return time.time() > exp_timestamp

    except Exception as e:
        logger.warning(f"Error checking token expiry: {e}")
        return True
