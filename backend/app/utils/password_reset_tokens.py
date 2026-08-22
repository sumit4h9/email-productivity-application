"""
Password reset token utilities for secure token generation and validation.
Separate from JWT token management to avoid conflicts.
"""

import hashlib
import hmac
import logging
import os
import secrets
from datetime import datetime, timedelta

from passlib.context import CryptContext

logger = logging.getLogger(__name__)

# Token configuration
RESET_TOKEN_LENGTH = 33  # 33 bytes = 264 bits of entropy, 44 chars when base64 encoded
RESET_TOKEN_EXPIRE_MINUTES = 10  # 10 minutes as specified
RESET_TOKEN_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"

# Use the same password hashing context as the main auth system
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Get secret key for token hashing (use JWT secret or generate one)
TOKEN_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback_secret_for_development_only")


def generate_reset_token() -> str:
    """
    Generate a cryptographically secure reset token.

    Returns:
        str: URL-safe base64 encoded token (44 characters)
    """
    # Generate 32 bytes of cryptographically secure random data

    # Convert to URL-safe base64 (44 characters)
    token = secrets.token_urlsafe(RESET_TOKEN_LENGTH)

    logger.debug(f"Generated reset token with {len(token)} characters")
    return token


def hash_reset_token(token: str) -> str:
    """
    Hash a reset token using HMAC-SHA256 for secure storage.

    Args:
        token: Plain text reset token

    Returns:
        str: Hashed token for database storage
    """
    if not token:
        raise ValueError("Token cannot be empty")

    # Use HMAC-SHA256 for token hashing (faster than bcrypt for short-lived tokens)
    hashed = hmac.new(
        TOKEN_SECRET_KEY.encode("utf-8"), token.encode("utf-8"), hashlib.sha256
    ).hexdigest()

    return hashed


def verify_reset_token(plain_token: str, hashed_token: str) -> bool:
    """
    Verify a plain text token against its hash.

    Args:
        plain_token: Plain text token to verify
        hashed_token: Stored hash to verify against

    Returns:
        bool: True if token matches, False otherwise
    """
    if not plain_token or not hashed_token:
        return False

    try:
        # Generate hash of the plain token
        expected_hash = hash_reset_token(plain_token)

        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(expected_hash, hashed_token)
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        return False


def get_token_expiry_time() -> datetime:
    """
    Get the expiry time for reset tokens.

    Returns:
        datetime: Expiry time (10 minutes from now)
    """
    return datetime.utcnow() + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)


def is_token_expired(expires_at: datetime) -> bool:
    """
    Check if a token has expired.

    Args:
        expires_at: Token expiry time

    Returns:
        bool: True if expired, False otherwise
    """
    return datetime.utcnow() > expires_at


def create_token_hash_pair() -> tuple[str, str, datetime]:
    """
    Create a token and its hash with expiry time.

    Returns:
        tuple: (plain_token, hashed_token, expires_at)
    """
    plain_token = generate_reset_token()
    hashed_token = hash_reset_token(plain_token)
    expires_at = get_token_expiry_time()

    return plain_token, hashed_token, expires_at


def validate_token_format(token: str) -> bool:
    """
    Validate the format of a reset token.

    Args:
        token: Token to validate

    Returns:
        bool: True if valid format, False otherwise
    """
    if not token or not isinstance(token, str):
        return False

    # Check length (URL-safe base64 of 32 bytes = 44 characters)
    if len(token) != 44:
        return False

    # Check if it contains only valid characters
    try:
        # URL-safe base64 characters: A-Z, a-z, 0-9, -, _
        for char in token:
            if char not in RESET_TOKEN_ALPHABET:
                return False
        return True
    except Exception:
        return False


def secure_token_cleanup():
    """
    Clean up expired tokens from memory (if any are cached).
    This is mainly for logging and monitoring purposes.
    """
    logger.debug("Performing secure token cleanup")


# Security constants for validation
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128
REQUIRED_PASSWORD_CATEGORIES = 2  # At least 2 of: lowercase, uppercase, digits, symbols


def validate_password_strength(password: str) -> dict:
    """
    Validate password strength for reset password functionality.
    Integrates with existing password validation patterns.

    Args:
        password: Password to validate

    Returns:
        dict: Validation result with ok, strength, score, warnings, suggestions
    """
    if not password or not isinstance(password, str):
        return {
            "ok": False,
            "strength": "invalid",
            "score": 0,
            "warnings": ["Password is required"],
            "suggestions": ["Enter a password"],
        }

    password = password.strip()
    length = len(password)
    warnings = []
    suggestions = []

    # Length validation
    if length < MIN_PASSWORD_LENGTH:
        warnings.append(f"Password must be at least {MIN_PASSWORD_LENGTH} characters")
        suggestions.append(f"Use at least {MIN_PASSWORD_LENGTH} characters")
    elif length > MAX_PASSWORD_LENGTH:
        warnings.append(f"Password must be no more than {MAX_PASSWORD_LENGTH} characters")
        suggestions.append(f"Use no more than {MAX_PASSWORD_LENGTH} characters")

    # Character category validation
    has_lower = any(c.islower() for c in password)
    has_upper = any(c.isupper() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_symbol = any(not c.isalnum() for c in password)

    categories = sum([has_lower, has_upper, has_digit, has_symbol])

    if categories < REQUIRED_PASSWORD_CATEGORIES:
        warnings.append(f"Use at least {REQUIRED_PASSWORD_CATEGORIES} character types")
        suggestions.append("Include uppercase, lowercase, numbers, or symbols")

    # Calculate strength score
    score = 0
    if length >= MIN_PASSWORD_LENGTH:
        score += 1
    if categories >= REQUIRED_PASSWORD_CATEGORIES:
        score += 1
    if length >= 12:
        score += 1
    if categories >= 3:
        score += 1

    strength_levels = ["very weak", "weak", "medium", "strong", "very strong"]
    strength = strength_levels[min(score, 4)]

    return {
        "ok": score >= 2,  # Require at least "medium" strength
        "strength": strength,
        "score": score,
        "warnings": warnings,
        "suggestions": suggestions,
    }


def hash_password_secure(password: str) -> str:
    """
    Hash password using the same method as the main authentication system.

    Args:
        password: Plain text password

    Returns:
        str: Hashed password
    """
    return pwd_context.hash(password)


def verify_password_secure(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password using the same method as the main authentication system.

    Args:
        plain_password: Plain text password
        hashed_password: Stored hash

    Returns:
        bool: True if password matches
    """
    return pwd_context.verify(plain_password, hashed_password)
