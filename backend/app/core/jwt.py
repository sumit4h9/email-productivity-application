# flake8: noqa: E501
import logging
import os
from datetime import datetime, timedelta
from typing import Optional, Tuple

import jwt  # type: ignore
import redis  # type: ignore
from dotenv import load_dotenv  # type: ignore

load_dotenv()
logger = logging.getLogger(__name__)

# Configuration
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "test_secret_key_for_development")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", 7))
CLOCK_SKEW_TOLERANCE = int(os.environ.get("CLOCK_SKEW_TOLERANCE", 30))  # seconds

# Automatic refresh configuration
AUTO_REFRESH_THRESHOLD_MINUTES = int(
    os.environ.get("AUTO_REFRESH_THRESHOLD_MINUTES", 5)
)  # Refresh if expiring within 5 minutes

# Redis setup with graceful degradation
redis_client = None
try:
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    redis_client = redis.Redis.from_url(
        REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
        retry_on_timeout=True,
        health_check_interval=30,
    )
    # Don't ping during import - let is_redis_available() handle the connection test
    logger.info("Redis client initialized (connection will be tested on first use)")
except Exception as e:
    logger.warning(f"Redis client initialization failed: {e}")
    redis_client = None


def is_redis_available() -> bool:
    """Check if Redis is available and healthy with timeout"""
    if not redis_client:
        return False
    try:
        # Use Redis client's built-in timeout instead of signal-based timeout
        # which doesn't work on Windows
        redis_client.ping()
        return True
    except Exception as e:
        logger.debug(f"Redis health check failed: {e}")
        return False


def create_access_token(data: dict):
    """Create a JWT access token with enhanced security"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    # Add standard JWT claims
    to_encode.update(
        {
            "exp": expire,
            "iat": datetime.utcnow(),
            "nbf": datetime.utcnow(),
            "type": "access",
            "iss": "auth_backend",
            "aud": "users",
        }
    )

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    # Store in Redis for blacklisting (with graceful degradation)
    if is_redis_available() and redis_client is not None:
        try:
            # Fix: Add null check and await if needed
            redis_client.setex(f"token:{encoded_jwt}", ACCESS_TOKEN_EXPIRE_MINUTES * 60, "valid")
        except Exception as e:
            logger.warning(f"Failed to store token in Redis: {e}")

    return encoded_jwt


def create_refresh_token(data: dict):
    """Create a JWT refresh token with enhanced security"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    # Add standard JWT claims
    to_encode.update(
        {
            "exp": expire,
            "iat": datetime.utcnow(),
            "nbf": datetime.utcnow(),
            "type": "refresh",
            "iss": "auth_backend",
            "aud": "users",
        }
    )

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    # Store in Redis (with graceful degradation)
    if is_redis_available() and redis_client is not None:
        try:
            # Fix: Add null check
            redis_client.setex(
                f"refresh:{encoded_jwt}", REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60, "valid"
            )
        except Exception as e:
            logger.warning(f"Failed to store refresh token in Redis: {e}")

    return encoded_jwt


def verify_token(token: str, token_type: Optional[str] = None) -> Optional[dict]:
    """Verify a JWT token with enhanced validation and graceful Redis degradation"""
    try:
        # Check if token is blacklisted (with graceful degradation)
        if is_redis_available() and redis_client is not None:
            try:
                # Fix: Add null check
                blacklisted = redis_client.get(f"blacklist:{token}")
                if blacklisted:
                    logger.warning("Token is blacklisted")
                    return None
            except Exception as e:
                logger.warning(f"Failed to check token blacklist: {e}")

        # Decode token with clock skew tolerance
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            audience="users",
            issuer="auth_backend",
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_iat": True,
                "verify_nbf": True,
                "require": ["exp", "iat", "nbf", "type"],
            },
            leeway=CLOCK_SKEW_TOLERANCE,
        )

        # Validate token type if specified
        if token_type and payload.get("type") != token_type:
            logger.warning(f"Invalid token type. Expected {token_type}, got {payload.get('type')}")
            return None

        # Validate issuer and audience
        if payload.get("iss") != "auth_backend" or payload.get("aud") != "users":
            logger.warning("Invalid token issuer or audience")
            return None

        return payload

    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return None
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        return None


def revoke_token(token: str):
    """Revoke a token by adding it to blacklist with graceful degradation"""
    if not is_redis_available():
        logger.warning("Redis not available, cannot revoke token")
        return

    try:
        # Decode token to get expiration
        payload = jwt.decode(
            token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_signature": False}
        )
        exp = payload.get("exp")

        if exp:
            # Calculate TTL for blacklist entry
            ttl = exp - datetime.utcnow().timestamp()
            if ttl > 0:
                redis_client.setex(f"blacklist:{token}", int(ttl), "revoked")
                logger.info("Token revoked successfully")
            else:
                logger.info("Token already expired, no need to revoke")
        else:
            # If no expiration, use default TTL
            redis_client.setex(f"blacklist:{token}", 24 * 60 * 60, "revoked")  # 24 hours
            logger.info("Token revoked with default TTL")

    except jwt.InvalidTokenError:
        logger.warning("Cannot revoke invalid token")
    except Exception as e:
        logger.error(f"Failed to revoke token: {e}")


def revoke_all_user_tokens(user_id: str):
    """Revoke all tokens for a specific user"""
    if not is_redis_available() or redis_client is None:
        logger.warning("Redis not available, cannot revoke user tokens")
        return

    try:
        # Find all tokens for this user (this is a simplified approach)
        # In production, you might want to maintain a separate index
        pattern = f"user_tokens:{user_id}:*"
        keys = redis_client.keys(pattern)

        if keys:
            redis_client.delete(*keys)
            logger.info(f"Revoked {len(keys)} tokens for user {user_id}")
        else:
            logger.info(f"No tokens found for user {user_id}")

    except Exception as e:
        logger.error(f"Failed to revoke user tokens: {e}")


def cleanup_expired_tokens():
    """Clean up expired tokens from Redis"""
    if not is_redis_available() or redis_client is None:
        logger.warning("Redis not available, cannot cleanup tokens")
        return

    try:
        # Get all token keys
        keys = redis_client.keys("token:*")
        if keys is not None:
            deleted_count = 0
            for key in keys:
                try:
                    # Check if token is expired
                    ttl = redis_client.ttl(key)
                    if ttl is not None and ttl <= 0:
                        redis_client.delete(key)
                        deleted_count += 1
                except Exception as e:
                    logger.warning(f"Error checking token {key}: {e}")

            logger.info(f"Cleaned up {deleted_count} expired tokens")
        else:
            logger.info("No tokens found for cleanup")

    except Exception as e:
        logger.error(f"Token cleanup failed: {e}")


def get_redis_memory_usage():
    """Get Redis memory usage information with error handling"""
    if not is_redis_available() or redis_client is None:
        return None

    try:
        info = redis_client.info("memory")
        return {
            "used_memory": info.get("used_memory", 0),
            "used_memory_human": info.get("used_memory_human", "0B"),
            "maxmemory": info.get("maxmemory", 0),
            "maxmemory_policy": info.get("maxmemory_policy", "noeviction"),
            "keyspace_hits": info.get("keyspace_hits", 0),
            "keyspace_misses": info.get("keyspace_misses", 0),
        }
    except Exception as e:
        logger.error(f"Failed to get Redis memory info: {e}")
        return None


def get_redis_health_status() -> dict:
    """Get Redis health status for monitoring with timeout"""
    import signal

    def timeout_handler(signum, frame):
        raise TimeoutError("Redis health check timeout")

    try:
        if not is_redis_available() or redis_client is None:
            return {"status": "disconnected", "error": "Redis not available"}

        # Set a 1-second timeout for Redis operations
        original_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(1)

        try:
            # Test Redis connection
            redis_client.ping()

            # Get Redis info
            info = redis_client.info()
            if info is not None:
                return {
                    "status": "connected",
                    "version": info.get("redis_version", "unknown"),
                    "used_memory": info.get("used_memory_human", "unknown"),
                    "connected_clients": info.get("connected_clients", 0),
                }
            else:
                return {"status": "connected", "info": "unavailable"}
        finally:
            # Cancel the alarm and restore original handler
            signal.alarm(0)
            signal.signal(signal.SIGALRM, original_handler)

    except TimeoutError:
        return {"status": "timeout", "error": "Redis connection timeout"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# =============================================================================
# AUTOMATIC TOKEN REFRESH FUNCTIONS
# =============================================================================


def decode_token_without_verification(token: str) -> Optional[dict]:
    """Decode a JWT token without verification for expiry checking"""
    try:
        payload = jwt.decode(
            token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_signature": False}
        )
        return payload
    except Exception as e:
        logger.warning(f"Failed to decode token without verification: {e}")
        return None


def is_token_expiring_soon(token: str, threshold_minutes: Optional[int] = None) -> bool:
    """Check if a token is expiring within the specified threshold"""
    if threshold_minutes is None:
        threshold_minutes = AUTO_REFRESH_THRESHOLD_MINUTES

    try:
        payload = decode_token_without_verification(token)
        if not payload:
            return True  # Assume expired if can't decode

        exp_timestamp = payload.get("exp")
        if not exp_timestamp:
            return True  # Assume expired if no expiry claim

        # Convert to datetime for comparison
        exp_time = datetime.fromtimestamp(exp_timestamp)
        threshold_time = datetime.utcnow() + timedelta(minutes=threshold_minutes)

        return exp_time <= threshold_time

    except Exception as e:
        logger.error(f"Error checking token expiry: {e}")
        return True  # Assume expired on error


def get_token_expiry_time(token: str) -> Optional[datetime]:
    """Get the expiry time of a token"""
    try:
        payload = decode_token_without_verification(token)
        if not payload:
            return None

        exp_timestamp = payload.get("exp")
        if not exp_timestamp:
            return None

        return datetime.fromtimestamp(exp_timestamp)

    except Exception as e:
        logger.error(f"Error getting token expiry time: {e}")
        return None


def rotate_refresh_token(refresh_token: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Rotate refresh token - create new access and refresh tokens, revoke old one

    Returns:
        tuple: (new_access_token, new_refresh_token, error_message)
    """
    try:
        # Verify the refresh token
        payload = verify_token(refresh_token, token_type="refresh")
        if not payload:
            return None, None, "Invalid refresh token"

        user_id = payload.get("sub")
        if not user_id:
            return None, None, "Invalid token payload"

        # Revoke the old refresh token
        revoke_token(refresh_token)

        # Create new tokens
        new_access_token = create_access_token({"sub": user_id})
        new_refresh_token = create_refresh_token({"sub": user_id})

        logger.info(f"Tokens rotated successfully for user {user_id}")
        return new_access_token, new_refresh_token, None

    except Exception as e:
        logger.error(f"Token rotation failed: {e}")
        return None, None, f"Token rotation error: {str(e)}"


def auto_refresh_tokens(
    access_token: str, refresh_token: str
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Automatically refresh tokens if access token is expiring soon

    Returns:
        tuple: (new_access_token, new_refresh_token, error_message)
    """
    try:
        # Check if access token needs refresh
        if not is_token_expiring_soon(access_token):
            return None, None, None  # No refresh needed

        # Perform token rotation
        return rotate_refresh_token(refresh_token)

    except Exception as e:
        logger.error(f"Auto refresh failed: {e}")
        return None, None, f"Auto refresh error: {str(e)}"
