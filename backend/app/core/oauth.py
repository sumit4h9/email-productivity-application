"""
OAuth configuration and Google client setup for email account integration
"""

import logging
import os
import re
import time
from typing import Dict, Optional, Tuple

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

load_dotenv()
logger = logging.getLogger(__name__)


def retry_on_rate_limit(max_retries: int = 3, delay: float = 1.0):
    """
    Decorator to retry API calls on rate limit errors

    Args:
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except HttpError as e:
                    if e.resp.status == 429 and attempt < max_retries:  # Rate limit
                        logger.warning(
                            f"Rate limit hit, retrying in {delay} seconds (attempt {attempt + 1}/{max_retries})"
                        )
                        time.sleep(delay * (2**attempt))  # Exponential backoff
                        continue
                    else:
                        raise
                except Exception as e:
                    if attempt < max_retries:
                        logger.warning(
                            f"API call failed, retrying in {delay} seconds (attempt {attempt + 1}/{max_retries}): {e}"
                        )
                        time.sleep(delay)
                        continue
                    else:
                        raise
            return None

        return wrapper

    return decorator


def validate_authorization_code(code: str) -> bool:
    """
    Validate authorization code format according to Google's specifications

    Args:
        code: Authorization code to validate

    Returns:
        bool: True if valid format, False otherwise
    """
    if not code or not isinstance(code, str):
        return False

    # Google auth codes typically start with "4/" and are 43-200 chars
    if not code.startswith("4/") or len(code) < 43 or len(code) > 200:
        return False

    # More restrictive pattern for Google's format
    if not re.match(r"^4/[0-9A-Za-z\-_\.]+$", code):
        return False

    return True


def validate_access_token(token: str) -> bool:
    """
    Validate access token format

    Args:
        token: Access token to validate

    Returns:
        bool: True if valid format, False otherwise
    """
    if not token or not isinstance(token, str):
        return False

    # Google access tokens are typically JWT format or long strings
    if len(token) < 20 or len(token) > 2000:
        return False

    # Check for valid characters (alphanumeric, hyphens, underscores, dots)
    if not re.match(r"^[A-Za-z0-9\-_\.]+$", token):
        return False

    return True


def validate_refresh_token(token: str) -> bool:
    """
    Validate refresh token format

    Args:
        token: Refresh token to validate

    Returns:
        bool: True if valid format, False otherwise
    """
    if not token or not isinstance(token, str):
        return False

    # Google refresh tokens are typically longer strings
    if len(token) < 50 or len(token) > 500:
        return False

    # Check for valid characters
    if not re.match(r"^[A-Za-z0-9\-_\.]+$", token):
        return False

    return True


def sanitize_user_info(user_info: Dict) -> Dict:
    """
    Sanitize user information to remove potentially sensitive data

    Args:
        user_info: Raw user info from Google

    Returns:
        Dict: Sanitized user information
    """
    sanitized = {}
    allowed_fields = ["id", "email", "name", "picture", "verified_email"]

    for field in allowed_fields:
        if field in user_info:
            value = user_info[field]
            if isinstance(value, str):
                # Basic sanitization - remove any potential script tags or special chars
                sanitized[field] = re.sub(r"<[^>]*>", "", value).strip()
            else:
                sanitized[field] = value

    return sanitized


def sanitize_exception_message(exception: Exception) -> str:
    """
    Sanitize exception messages to prevent information disclosure

    Args:
        exception: Exception to sanitize

    Returns:
        str: Sanitized error message
    """
    # Define safe error messages for common exceptions
    safe_messages = {
        "ValueError": "Invalid input provided",
        "RuntimeError": "Service temporarily unavailable",
        "ConnectionError": "Network connection failed",
        "TimeoutError": "Request timed out",
        "PermissionError": "Access denied",
        "FileNotFoundError": "Resource not found",
        "KeyError": "Invalid configuration",
        "TypeError": "Invalid data type",
        "AttributeError": "Invalid operation",
        "ImportError": "Service configuration error",
    }

    # Get the exception type name
    exception_type = type(exception).__name__

    # Return safe message if available, otherwise generic message
    if exception_type in safe_messages:
        return safe_messages[exception_type]
    else:
        # For unknown exceptions, return a generic message
        return "An unexpected error occurred"


def log_exception_safely(exception: Exception, context: str = "") -> None:
    """
    Log exceptions safely without exposing sensitive information

    Args:
        exception: Exception to log
        context: Additional context for logging
    """
    sanitized_message = sanitize_exception_message(exception)
    exception_type = type(exception).__name__

    if context:
        logger.error(f"{context}: {sanitized_message} (Exception type: {exception_type})")
    else:
        logger.error(f"{sanitized_message} (Exception type: {exception_type})")

    # Log the full exception details at debug level for debugging
    logger.debug(f"Full exception details: {exception}", exc_info=True)


# OAuth Configuration
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.environ.get(
    "GOOGLE_REDIRECT_URI", "http://localhost:3000/auth/google/callback"
)


def _get_client_config() -> Dict:
    """
    Get Google OAuth client configuration

    Returns:
        Dict: Client configuration for Google OAuth
    """
    return {
        "web": {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/v2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [GOOGLE_REDIRECT_URI],
        }
    }


# Gmail API Configuration - Full access for complete email management
GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",  # Read, send, delete, modify labels
    "https://www.googleapis.com/auth/gmail.send",  # Send emails
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "openid",
]

# OAuth Flow Configuration
OAUTH_CONFIG = {
    "client_id": GOOGLE_CLIENT_ID,
    "client_secret": GOOGLE_CLIENT_SECRET,
    "redirect_uri": GOOGLE_REDIRECT_URI,
    "scope": " ".join(GMAIL_SCOPES),
    "access_type": "offline",
    "prompt": "consent",  # Force consent to ensure refresh token
}


def get_google_oauth_url() -> str:
    """
    Generate Google OAuth authorization URL

    Returns:
        str: Authorization URL for Google OAuth flow

    Raises:
        ValueError: If OAuth configuration is invalid
        RuntimeError: If OAuth URL generation fails
    """
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        logger.error("Google OAuth credentials not configured")
        raise ValueError("OAuth service is not properly configured")

    try:
        flow = Flow.from_client_config(
            _get_client_config(),
            scopes=GMAIL_SCOPES,
        )
        flow.redirect_uri = GOOGLE_REDIRECT_URI

        authorization_url, _ = flow.authorization_url(
            access_type="offline", prompt="consent", include_granted_scopes="true"
        )

        logger.info("Generated Google OAuth authorization URL")
        return authorization_url

    except Exception as e:
        log_exception_safely(e, "Failed to generate Google OAuth URL")
        raise RuntimeError("Failed to initialize OAuth flow")


def exchange_code_for_tokens(authorization_code: str) -> Tuple[Credentials, Dict]:
    """
    Exchange authorization code for access and refresh tokens

    Args:
        authorization_code: Authorization code from OAuth callback

    Returns:
        Tuple of (Credentials object, user_info dict)

    Raises:
        ValueError: If authorization code is invalid or OAuth not configured
        RuntimeError: If token exchange fails
    """
    if not validate_authorization_code(authorization_code):
        logger.error("Invalid authorization code format provided")
        raise ValueError("Invalid authorization code")

    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        logger.error("Google OAuth credentials not configured")
        raise ValueError("OAuth service is not properly configured")

    try:
        flow = Flow.from_client_config(
            _get_client_config(),
            scopes=GMAIL_SCOPES,
        )
        flow.redirect_uri = GOOGLE_REDIRECT_URI

        # Exchange code for tokens
        flow.fetch_token(code=authorization_code)
        credentials = flow.credentials

        # Get user info
        user_info = get_user_info(credentials)
        sanitized_user_info = sanitize_user_info(user_info)

        logger.info(
            f"Successfully exchanged code for tokens for user: {sanitized_user_info.get('email', 'unknown')}"
        )
        return credentials, sanitized_user_info

    except Exception as e:
        # Handle specific OAuth errors
        from google_auth_oauthlib.flow import InvalidGrantError
        if isinstance(e, InvalidGrantError):
            logger.error(f"Invalid grant error for authorization code: {type(e).__name__}")
            raise ValueError("Authorization code is invalid, expired, or has already been used")
        else:
            log_exception_safely(e, "Failed to exchange authorization code")
            raise RuntimeError("Failed to complete OAuth authentication")


@retry_on_rate_limit(max_retries=3, delay=1.0)
def get_user_info(credentials: Credentials) -> Dict:
    """
    Get user information from Google using credentials

    Args:
        credentials: Google OAuth credentials

    Returns:
        Dict containing user information
    """
    try:
        service = build("oauth2", "v2", credentials=credentials)
        user_info = service.userinfo().get().execute()

        return {
            "id": user_info.get("id"),
            "email": user_info.get("email"),
            "name": user_info.get("name"),
            "picture": user_info.get("picture"),
            "verified_email": user_info.get("verified_email", False),
        }

    except Exception as e:
        log_exception_safely(e, "Failed to get user info")
        raise


def refresh_credentials(credentials: Credentials) -> Optional[Credentials]:
    """
    Refresh expired Google OAuth credentials

    Args:
        credentials: Expired or expiring credentials

    Returns:
        Refreshed credentials if successful, original credentials if not expired,
        None if refresh failed or no refresh token available
    """
    try:
        # If credentials are not expired, return them as-is
        if not credentials.expired:
            logger.debug("Credentials are still valid, no refresh needed")
            return credentials

        # If expired but no refresh token, cannot refresh
        if not credentials.refresh_token:
            logger.warning("Cannot refresh credentials: no refresh token available")
            return None

        # Attempt to refresh
        credentials.refresh(Request())
        logger.info("Successfully refreshed Google OAuth credentials")
        return credentials

    except Exception as e:
        log_exception_safely(e, "Failed to refresh credentials")
        return None


def validate_credentials(credentials: Credentials) -> bool:
    """
    Test if credentials work by making a simple API call

    Args:
        credentials: Google OAuth credentials to test

    Returns:
        bool: True if credentials are valid, False otherwise
    """
    try:
        # Try to get user info as a simple test
        user_info = get_user_info(credentials)
        if user_info and user_info.get("email"):
            logger.info(f"Credentials validated for user: {user_info.get('email')}")
            return True
        else:
            logger.warning("Credentials test failed: no user info returned")
            return False
    except Exception as e:
        log_exception_safely(e, "Credentials validation failed")
        return False


def create_gmail_service(credentials: Credentials):
    """
    Create Gmail API service instance

    Args:
        credentials: Google OAuth credentials

    Returns:
        Gmail API service instance
    """
    try:
        service = build("gmail", "v1", credentials=credentials)
        logger.info("Successfully created Gmail API service")
        return service

    except Exception as e:
        log_exception_safely(e, "Failed to create Gmail service")
        raise


def validate_oauth_config() -> bool:
    """
    Validate that OAuth configuration is properly set

    Returns:
        bool: True if configuration is valid, False otherwise
    """
    required_vars = ["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET"]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]

    if missing_vars:
        logger.error(f"Missing required OAuth environment variables: {missing_vars}")
        return False

    # Validate redirect URI format
    if not GOOGLE_REDIRECT_URI.startswith(("http://localhost", "https://")):
        logger.error("Invalid redirect URI format - must start with http://localhost or https://")
        return False

    # Validate client ID format (Google client IDs typically start with numbers and contain dots)
    if not re.match(r"^[0-9]+-[0-9A-Za-z]+\.apps\.googleusercontent\.com$", GOOGLE_CLIENT_ID):
        logger.warning(
            "Client ID format may be invalid - should be in format: number-string.apps.googleusercontent.com"
        )

    logger.info("OAuth configuration validation passed")
    return True
