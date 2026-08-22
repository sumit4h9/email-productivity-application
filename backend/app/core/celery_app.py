"""
Celery application configuration for background task processing
"""

import logging
import os
import re
from urllib.parse import urlparse, urlunparse

from celery import Celery
from celery.schedules import crontab
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Redis configuration
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD")


def _sanitize_redis_url(url: str) -> str:
    """
    Sanitize Redis URL for logging (remove password)

    Args:
        url: Redis URL to sanitize

    Returns:
        str: Sanitized URL without password
    """
    try:
        parsed = urlparse(url)
        if parsed.password:
            # Replace password with ***
            netloc = f"{parsed.username}:***@{parsed.hostname}"
            if parsed.port:
                netloc += f":{parsed.port}"
            sanitized = urlunparse(
                (parsed.scheme, netloc, parsed.path, parsed.params, parsed.query, parsed.fragment)
            )
            return sanitized
        return url
    except Exception:
        # If parsing fails, return a generic sanitized version
        return "redis://***:***@***"


def _construct_secure_redis_url(base_url: str, password: str = None) -> str:
    """
    Securely construct Redis URL with password

    Args:
        base_url: Base Redis URL
        password: Optional password

    Returns:
        str: Secure Redis URL

    Raises:
        ValueError: If URL format is invalid
    """
    if not base_url or not isinstance(base_url, str):
        raise ValueError("Invalid Redis URL provided")

    # Validate URL format
    if not re.match(r"^redis://[a-zA-Z0-9.-]+(:\d+)?(/\d+)?$", base_url):
        raise ValueError("Invalid Redis URL format")

    if not password:
        return base_url

    try:
        parsed = urlparse(base_url)

        # Construct secure URL with password
        netloc = f"{parsed.username or 'default'}:{password}@{parsed.hostname}"
        if parsed.port:
            netloc += f":{parsed.port}"

        secure_url = urlunparse(
            (parsed.scheme, netloc, parsed.path, parsed.params, parsed.query, parsed.fragment)
        )
        return secure_url

    except Exception as e:
        raise ValueError(f"Failed to construct secure Redis URL: {e}")


# Construct secure Redis URLs
try:
    CELERY_BROKER_URL = _construct_secure_redis_url(REDIS_URL, REDIS_PASSWORD)
    CELERY_RESULT_BACKEND = _construct_secure_redis_url(REDIS_URL, REDIS_PASSWORD)
except ValueError as e:
    logger.error(f"Redis URL configuration error: {e}")
    raise

# Create Celery application
celery_app = Celery(
    "axnore_email_sync",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.email_sync",
        "app.tasks.oauth_cleanup",
        "app.tasks.health_check",
    ],
)

# Celery configuration
celery_app.conf.update(
    # Task execution
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Task routing
    task_routes={
        "app.tasks.email_sync.*": {"queue": "email_sync"},
        "app.tasks.oauth_cleanup.*": {"queue": "oauth_cleanup"},
        "app.tasks.health_check.*": {"queue": "health_check"},
    },
    # Task execution limits
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    # Result backend settings
    result_expires=3600,  # 1 hour
    result_persistent=True,
    # Task retry settings
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
    # Worker settings
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=False,
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
    # Security
    worker_hijack_root_logger=False,
    worker_log_color=False,
    # Connection settings
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,
    broker_connection_retry_delay=1.0,
    # Redis specific settings
    broker_transport_options={
        "visibility_timeout": 3600,
        "fanout_prefix": True,
        "fanout_patterns": True,
        "socket_connect_timeout": 5,
        "socket_timeout": 5,
        "retry_on_timeout": True,
        "health_check_interval": 30,
    },
    result_backend_transport_options={
        "socket_connect_timeout": 5,
        "socket_timeout": 5,
        "retry_on_timeout": True,
        "health_check_interval": 30,
    },
)

# Task time limits
celery_app.conf.task_annotations = {
    "app.tasks.email_sync.sync_gmail_account": {
        "time_limit": 300,  # 5 minutes
        "soft_time_limit": 240,  # 4 minutes
    },
    "app.tasks.email_sync.sync_all_accounts": {
        "time_limit": 1800,  # 30 minutes
        "soft_time_limit": 1500,  # 25 minutes
    },
    "app.tasks.email_sync.periodic_sync_all_accounts": {
        "time_limit": 1800,  # 30 minutes
        "soft_time_limit": 1500,  # 25 minutes
    },
    "app.tasks.oauth_cleanup.cleanup_expired_tokens": {
        "time_limit": 600,  # 10 minutes
        "soft_time_limit": 480,  # 8 minutes
    },
    "app.tasks.health_check.check_system_health": {
        "time_limit": 30,  # 30 seconds
        "soft_time_limit": 25,  # 25 seconds
    },
}

# Celery Beat Schedule Configuration

celery_app.conf.beat_schedule = {
    # Sync all accounts every 3 minutes
    "periodic-sync-all-accounts": {
        "task": "app.tasks.email_sync.periodic_sync_all_accounts",
        "schedule": crontab(minute="*/3"),  # Every 3 minutes
        "options": {
            "queue": "email_sync",
            "priority": 5,  # Lower priority than manual sync
        },
    },
    # Cleanup expired tokens daily at 2 AM
    "cleanup-expired-tokens-daily": {
        "task": "app.tasks.oauth_cleanup.cleanup_expired_tokens",
        "schedule": crontab(hour=2, minute=0),  # Daily at 2 AM
        "options": {
            "queue": "oauth_cleanup",
        },
    },
    # Health check every 5 minutes
    "system-health-check": {
        "task": "app.tasks.health_check.check_system_health",
        "schedule": crontab(minute="*/5"),  # Every 5 minutes
        "options": {
            "queue": "health_check",
        },
    },
    # Sync active accounts every 30 minutes (less frequent)
    "sync-active-accounts": {
        "task": "app.tasks.email_sync.sync_active_accounts",
        "schedule": crontab(minute="*/30"),  # Every 30 minutes
        "options": {
            "queue": "email_sync",
            "priority": 3,  # Medium priority
        },
    },
}

# Beat schedule timezone
celery_app.conf.timezone = "UTC"


def get_celery_app() -> Celery:
    """
    Get the configured Celery application instance

    Returns:
        Celery: Configured Celery application
    """
    return celery_app


def validate_celery_config() -> bool:
    """
    Validate Celery configuration with secure connection testing

    Returns:
        bool: True if configuration is valid, False otherwise
    """
    try:
        # Test Redis connection with secure parsing
        import socket

        from redis import Redis

        # Parse Redis URL securely
        parsed = urlparse(CELERY_BROKER_URL)

        # Extract connection parameters
        host = parsed.hostname or "localhost"
        port = parsed.port or 6379
        password = parsed.password
        username = parsed.username

        # Validate hostname format
        if not re.match(r"^[a-zA-Z0-9.-]+$", host):
            raise ValueError("Invalid hostname format")

        # Validate port range
        if not (1 <= port <= 65535):
            raise ValueError("Invalid port number")

        # Test connection with timeouts
        redis_client = Redis(
            host=host,
            port=port,
            password=password,
            username=username,
            decode_responses=True,
            socket_connect_timeout=5,  # 5 second connection timeout
            socket_timeout=5,  # 5 second socket timeout
            health_check_interval=30,  # Health check every 30 seconds
        )

        # Test connection with timeout
        redis_client.ping()

        logger.info(
            f"Celery configuration validation passed for {_sanitize_redis_url(CELERY_BROKER_URL)}"
        )
        return True

    except socket.timeout:
        logger.error("Redis connection timeout - check if Redis is running and accessible")
        return False
    except ConnectionRefusedError:
        logger.error("Redis connection refused - check if Redis is running")
        return False
    except Exception as e:
        logger.error(f"Celery configuration validation failed: {e}")
        return False


def get_celery_health_status() -> dict:
    """
    Get Celery system health status (sanitized for security)
    Uses timeout to prevent hanging when Redis is unavailable

    Returns:
        dict: Health status information without sensitive data
    """
    import signal

    def timeout_handler(signum, frame):
        raise TimeoutError("Celery health check timeout")

    try:
        # Set a 2-second timeout for the health check
        original_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(2)

        try:
            # Get Celery stats with timeout
            stats = celery_app.control.inspect().stats()

            # Get active tasks
            active_tasks = celery_app.control.inspect().active()

            # Get scheduled tasks
            scheduled_tasks = celery_app.control.inspect().scheduled()

            # Get registered tasks
            registered_tasks = celery_app.control.inspect().registered()

            # Count tasks for summary
            total_active = sum(len(tasks) for tasks in (active_tasks or {}).values())
            total_scheduled = sum(len(tasks) for tasks in (scheduled_tasks or {}).values())
            total_workers = len(stats) if stats else 0

            return {
                "status": "healthy",
                "broker_type": "redis",
                "broker_url_sanitized": _sanitize_redis_url(CELERY_BROKER_URL),
                "result_backend_sanitized": _sanitize_redis_url(CELERY_RESULT_BACKEND),
                "workers": {
                    "total": total_workers,
                    "active": total_workers > 0,
                },
                "tasks": {
                    "active_count": total_active,
                    "scheduled_count": total_scheduled,
                    "registered_count": (
                        len(registered_tasks.get(list(registered_tasks.keys())[0], []))
                        if registered_tasks
                        else 0
                    ),
                },
                "queues": {
                    "email_sync": "configured",
                    "oauth_cleanup": "configured",
                    "health_check": "configured",
                },
            }
        finally:
            # Cancel the alarm and restore original handler
            signal.alarm(0)
            signal.signal(signal.SIGALRM, original_handler)

    except TimeoutError:
        logger.warning("Celery health check timed out - Redis may be unavailable")
        return {
            "status": "unhealthy",
            "error": "Health check timeout - Redis unavailable",
            "broker_type": "redis",
            "broker_url_sanitized": _sanitize_redis_url(CELERY_BROKER_URL),
            "result_backend_sanitized": _sanitize_redis_url(CELERY_RESULT_BACKEND),
        }
    except Exception as e:
        logger.error(f"Failed to get Celery health status: {e}")
        return {
            "status": "unhealthy",
            "error": "Service temporarily unavailable",
            "broker_type": "redis",
            "broker_url_sanitized": _sanitize_redis_url(CELERY_BROKER_URL),
            "result_backend_sanitized": _sanitize_redis_url(CELERY_RESULT_BACKEND),
        }


if __name__ == "__main__":
    # Test Celery configuration
    if validate_celery_config():
        print("✅ Celery configuration is valid")
        print(f"Broker URL: {_sanitize_redis_url(CELERY_BROKER_URL)}")
        print(f"Result Backend: {_sanitize_redis_url(CELERY_RESULT_BACKEND)}")
    else:
        print("❌ Celery configuration is invalid")
        exit(1)
