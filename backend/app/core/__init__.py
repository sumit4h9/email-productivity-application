"""
Core module for authentication and OAuth functionality
"""

# Import Celery functions
from app.core.celery_app import (
    get_celery_app,
    get_celery_health_status,
    validate_celery_config,
)

# Import JWT functions
from app.core.jwt import (
    auto_refresh_tokens,
    create_access_token,
    create_refresh_token,
    get_redis_health_status,
    revoke_token,
    verify_token,
)

# Import OAuth functions
from app.core.oauth import (
    create_gmail_service,
    exchange_code_for_tokens,
    get_google_oauth_url,
    get_user_info,
    log_exception_safely,
    refresh_credentials,
    sanitize_exception_message,
    sanitize_user_info,
    validate_access_token,
    validate_authorization_code,
    validate_credentials,
    validate_oauth_config,
    validate_refresh_token,
)

__all__ = [
    # JWT functions
    "auto_refresh_tokens",
    "create_access_token",
    "create_refresh_token",
    "get_redis_health_status",
    "revoke_token",
    "verify_token",
    # OAuth functions
    "create_gmail_service",
    "exchange_code_for_tokens",
    "get_google_oauth_url",
    "get_user_info",
    "log_exception_safely",
    "refresh_credentials",
    "sanitize_exception_message",
    "sanitize_user_info",
    "validate_access_token",
    "validate_authorization_code",
    "validate_credentials",
    "validate_oauth_config",
    "validate_refresh_token",
    # Celery functions
    "get_celery_app",
    "get_celery_health_status",
    "validate_celery_config",
]
