"""
Rate limiting middleware for API endpoints with multi-factor protection
"""

import logging
import time
from collections import defaultdict
from functools import wraps
from typing import Callable, Dict, List, Tuple

from fastapi import HTTPException, Request, status  # type: ignore
from starlette.middleware.base import BaseHTTPMiddleware  # type: ignore

from app.core.jwt import is_redis_available, redis_client

logger = logging.getLogger(__name__)


class RateLimiter:
    def __init__(self):
        self.memory_store: Dict[str, List[float]] = defaultdict(list)
        self.max_memory_entries = 10000  # Prevent memory exhaustion

    def _get_client_identifier(self, request: Request) -> str:
        """Get a unique identifier for the client using multiple factors"""
        # Get real IP address (handles proxies)
        real_ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        if not real_ip:
            real_ip = request.headers.get("x-real-ip", "")
        if not real_ip:
            real_ip = request.client.host if request.client else "unknown"

        # Get user agent
        user_agent = request.headers.get("user-agent", "unknown")

        # Get additional factors
        accept_language = request.headers.get("accept-language", "unknown")

        # Create a composite identifier
        identifier = f"{real_ip}:{user_agent[:50]}:{accept_language[:20]}"
        return identifier

    def _get_rate_limit_key(self, request: Request, identifier: str) -> str:
        """Generate rate limit key based on endpoint and client"""
        endpoint = request.url.path
        method = request.method

        # Different keys for different endpoints
        if endpoint.startswith("/auth/login"):
            return f"rate_limit:login:{identifier}"
        elif endpoint.startswith("/auth/signup"):
            return f"rate_limit:signup:{identifier}"
        elif endpoint.startswith("/auth/refresh"):
            return f"rate_limit:refresh:{identifier}"
        elif endpoint.startswith("/auth/signup/init"):
            return f"rate_limit:signup_init:{identifier}"
        elif endpoint.startswith("/auth/signup/verify"):
            return f"rate_limit:signup_verify:{identifier}"
        elif endpoint.startswith("/auth/login/init"):
            return f"rate_limit:login_init:{identifier}"
        elif endpoint.startswith("/auth/login/verify"):
            return f"rate_limit:login_verify:{identifier}"
        else:
            return f"rate_limit:general:{identifier}:{method}:{endpoint}"

    def _get_rate_limit_config(self, endpoint: str) -> Tuple[int, int]:
        """Get rate limit configuration for different endpoints"""
        configs = {
            "/auth/signup/init": (10, 3600),  # 5 signup init attempts per hour
            "/auth/signup/verify": (10, 300),  # 5 signup verify attempts per 5 minutes
            "/auth/login/init": (10, 3600),  # 5 login init attempts per hour
            "/auth/login/verify": (10, 300),  # 5 login verify attempts per 5 minutes
            "/auth/login": (100, 300),  # 5 attempts per 5 minutes
            "/auth/signup": (1000, 3600),  # 3 signups per hour
            "/auth/refresh": (100, 60),  # 10 refreshes per minute
            "/auth/": (100, 300),  # 20 auth requests per 5 minutes
        }

        for pattern, config in configs.items():
            if endpoint.startswith(pattern):
                return config

        # Default rate limit
        return (100, 60)  # 100 requests per minute

    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> bool:
        """
        Check if request is allowed based on rate limiting with graceful Redis degradation
        """
        current_time = time.time()
        requests = []

        # Try Redis first
        if is_redis_available() and redis_client is not None:
            try:
                # Fix: Add null check and handle async properly
                requests_str = redis_client.get(key)
                if requests_str:
                    # Fix: Handle both string and bytes responses
                    if isinstance(requests_str, bytes):
                        requests_str = requests_str.decode("utf-8")
                    requests = [float(t) for t in requests_str.split(",")]
            except Exception as e:
                logger.warning(f"Redis error in rate limiting: {e}")
                # Fallback to memory
                requests = self.memory_store.get(key, [])
        else:
            # Fallback to memory
            requests = self.memory_store.get(key, [])

        # Remove old requests outside the window
        requests = [req_time for req_time in requests if current_time - req_time < window_seconds]

        # Check if limit exceeded
        if len(requests) >= max_requests:
            return False

        # Add current request
        requests.append(current_time)

        # Store updated requests
        if is_redis_available() and redis_client is not None:
            try:
                # Store as comma-separated string in Redis
                requests_str = ",".join(map(str, requests))
                redis_client.setex(key, window_seconds, requests_str)
            except Exception as e:
                logger.warning(f"Redis error storing rate limit: {e}")
                # Fallback to memory
                self.memory_store[key] = requests
                # Limit memory store size
                if len(self.memory_store) > self.max_memory_entries:
                    # Remove oldest keys
                    oldest_key = min(
                        self.memory_store.keys(), key=lambda k: min(self.memory_store[k], default=0)
                    )
                    del self.memory_store[oldest_key]
        else:
            # Store in memory
            self.memory_store[key] = requests
            # Limit memory store size
            if len(self.memory_store) > self.max_memory_entries:
                # Remove oldest keys
                oldest_key = min(
                    self.memory_store.keys(), key=lambda k: min(self.memory_store[k], default=0)
                )
                del self.memory_store[oldest_key]

        return True

    def get_remaining_requests(self, key: str, max_requests: int, window_seconds: int) -> int:
        """Get remaining requests for the current window"""
        current_time = time.time()
        requests = []

        # Try Redis first
        if is_redis_available() and redis_client is not None:
            try:
                requests_str = redis_client.get(key)
                if requests_str:
                    # Fix: Handle both string and bytes responses
                    if isinstance(requests_str, bytes):
                        requests_str = requests_str.decode("utf-8")
                    requests = [float(t) for t in requests_str.split(",")]
            except Exception:
                requests = self.memory_store.get(key, [])
        else:
            requests = self.memory_store.get(key, [])

        # Remove old requests
        requests = [req_time for req_time in requests if current_time - req_time < window_seconds]

        return max(0, max_requests - len(requests))


rate_limiter = RateLimiter()


def rate_limit(max_requests: int, window_seconds: int):
    """
    Decorator to apply rate limiting to specific endpoints

    Args:
        max_requests: Maximum number of requests allowed in the window
        window_seconds: Time window in seconds

    Usage:
        @rate_limit(3, 3600)  # 3 requests per hour
        async def signup(...):
            ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find the request object in args or kwargs
            request = None
            for arg in args:
                if hasattr(arg, "headers") and hasattr(arg, "url"):
                    request = arg
                    break

            if not request:
                for value in kwargs.values():
                    if hasattr(value, "headers") and hasattr(value, "url"):
                        request = value
                        break

            if not request:
                logger.warning("Could not find request object for rate limiting")
                return await func(*args, **kwargs)

            # Get client identifier
            client_id = rate_limiter._get_client_identifier(request)

            # Generate rate limit key for this specific endpoint
            endpoint = request.url.path
            method = request.method
            rate_limit_key = f"rate_limit:decorator:{endpoint}:{method}:{client_id}"

            # Check rate limit
            if not rate_limiter.is_allowed(rate_limit_key, max_requests, window_seconds):
                # Get remaining requests for retry-after header
                remaining = rate_limiter.get_remaining_requests(
                    rate_limit_key, max_requests, window_seconds
                )

                # Calculate retry-after time
                retry_after = int(window_seconds - (time.time() % window_seconds))

                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": "Too many requests",
                        "retry_after": retry_after,
                        "limit": max_requests,
                        "window": window_seconds,
                    },
                    headers={
                        "Retry-After": str(retry_after),
                        "X-RateLimit-Limit": str(max_requests),
                        "X-RateLimit-Remaining": str(remaining),
                        "X-RateLimit-Reset": str(int(time.time() + retry_after)),
                    },
                )

            # Add rate limit headers to response
            response = await func(*args, **kwargs)

            # Add rate limit headers if response has headers attribute
            if hasattr(response, "headers"):
                remaining = rate_limiter.get_remaining_requests(
                    rate_limit_key, max_requests, window_seconds
                )
                response.headers["X-RateLimit-Limit"] = str(max_requests)
                response.headers["X-RateLimit-Remaining"] = str(remaining)
                response.headers["X-RateLimit-Reset"] = str(int(time.time() + window_seconds))

            return response

        return wrapper

    return decorator


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Enhanced rate limiting middleware with multi-factor protection"""

    async def dispatch(self, request: Request, call_next):
        try:
            # Get client identifier
            client_id = rate_limiter._get_client_identifier(request)

            # Get rate limit key
            rate_limit_key = rate_limiter._get_rate_limit_key(request, client_id)

            # Get rate limit configuration
            max_requests, window = rate_limiter._get_rate_limit_config(request.url.path)

            # Check rate limit
            if not rate_limiter.is_allowed(rate_limit_key, max_requests, window):
                # Get remaining requests for retry-after header
                remaining = rate_limiter.get_remaining_requests(
                    rate_limit_key, max_requests, window
                )

                # Calculate retry-after time
                retry_after = int(window - (time.time() % window))

                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": "Too many requests",
                        "retry_after": retry_after,
                        "limit": max_requests,
                        "window": window,
                    },
                    headers={
                        "Retry-After": str(retry_after),
                        "X-RateLimit-Limit": str(max_requests),
                        "X-RateLimit-Remaining": str(remaining),
                        "X-RateLimit-Reset": str(int(time.time() + retry_after)),
                    },
                )

            # Add rate limit headers to response
            response = await call_next(request)

            # Add rate limit headers
            remaining = rate_limiter.get_remaining_requests(rate_limit_key, max_requests, window)
            response.headers["X-RateLimit-Limit"] = str(max_requests)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(int(time.time() + window))

            return response

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # Allow request to continue if rate limiting fails
            return await call_next(request)


def get_rate_limit_status() -> dict:
    """Get rate limiting status for monitoring"""
    try:
        if is_redis_available() and redis_client is not None:
            # Fix: Add null check and handle response properly
            keys = redis_client.keys("rate_limit:*")
            if keys is not None:
                return {"status": "redis", "active_keys": len(keys), "memory_fallback": False}
            else:
                return {"status": "redis", "active_keys": 0, "memory_fallback": False}
        else:
            # Get memory store status
            memory_keys = len(rate_limiter.memory_store)
            return {
                "status": "memory",
                "active_keys": memory_keys,
                "memory_fallback": True,
                "max_memory_entries": rate_limiter.max_memory_entries,
            }
    except Exception as e:
        return {"status": "error", "error": str(e)}
