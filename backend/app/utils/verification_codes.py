"""
Verification code utilities for secure code generation and validation.
Follows the same patterns as password reset tokens for consistency.
"""

import hashlib
import hmac
import logging
import os
import secrets
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Verification code configuration
VERIFICATION_CODE_LENGTH = 6  # 6-digit numeric codes as specified
VERIFICATION_CODE_EXPIRE_MINUTES = 10  # 10 minutes as specified
VERIFICATION_CODE_ALPHABET = "0123456789"  # Only numeric digits
MAX_ATTEMPTS = 5  # Maximum attempts per code

# Get secret key for code hashing (use JWT secret or generate one)
CODE_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback_secret_for_development_only")


def generate_verification_code() -> str:
    """
    Generate a cryptographically secure 6-digit verification code.

    Returns:
        str: 6-digit numeric code (000000-999999)
    """
    # Generate 6 random digits
    code = ""
    for _ in range(VERIFICATION_CODE_LENGTH):
        code += secrets.choice(VERIFICATION_CODE_ALPHABET)

    logger.debug(f"Generated verification code with {len(code)} digits")
    return code


def hash_verification_code(code: str) -> str:
    """
    Hash a verification code using HMAC-SHA256 for secure storage.

    Args:
        code: Plain text verification code

    Returns:
        str: Hashed code for database storage
    """
    if not code:
        raise ValueError("Code cannot be empty")

    # Use HMAC-SHA256 for code hashing (faster than bcrypt for short-lived codes)
    hashed = hmac.new(
        CODE_SECRET_KEY.encode("utf-8"), code.encode("utf-8"), hashlib.sha256
    ).hexdigest()

    return hashed


def verify_verification_code(plain_code: str, hashed_code: str) -> bool:
    """
    Verify a plain text code against its hash.

    Args:
        plain_code: Plain text code to verify
        hashed_code: Stored hash to verify against

    Returns:
        bool: True if code matches, False otherwise
    """
    if not plain_code or not hashed_code:
        return False

    try:
        # Generate hash of the plain code
        expected_hash = hash_verification_code(plain_code)

        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(expected_hash, hashed_code)
    except Exception as e:
        logger.error(f"Code verification error: {e}")
        return False


def get_code_expiry_time() -> datetime:
    """
    Get the expiry time for verification codes.

    Returns:
        datetime: Expiry time (10 minutes from now)
    """
    return datetime.utcnow() + timedelta(minutes=VERIFICATION_CODE_EXPIRE_MINUTES)


def is_code_expired(expires_at: datetime) -> bool:
    """
    Check if a verification code has expired.

    Args:
        expires_at: Code expiry time

    Returns:
        bool: True if expired, False otherwise
    """
    return datetime.utcnow() > expires_at


def create_code_hash_pair() -> tuple[str, str, datetime]:
    """
    Create a verification code and its hash with expiry time.

    Returns:
        tuple: (plain_code, hashed_code, expires_at)
    """
    plain_code = generate_verification_code()
    hashed_code = hash_verification_code(plain_code)
    expires_at = get_code_expiry_time()

    return plain_code, hashed_code, expires_at


def validate_code_format(code: str) -> bool:
    """
    Validate the format of a verification code.

    Args:
        code: Code to validate

    Returns:
        bool: True if valid format, False otherwise
    """
    if not code or not isinstance(code, str):
        return False

    # Check length (6 digits)
    if len(code) != VERIFICATION_CODE_LENGTH:
        return False

    # Check if it contains only valid characters (digits)
    try:
        for char in code:
            if char not in VERIFICATION_CODE_ALPHABET:
                return False
        return True
    except Exception:
        return False


def is_max_attempts_reached(attempts: int) -> bool:
    """
    Check if maximum attempts have been reached for a verification code.

    Args:
        attempts: Current number of attempts

    Returns:
        bool: True if max attempts reached, False otherwise
    """
    return attempts >= MAX_ATTEMPTS


def secure_code_cleanup():
    """
    Clean up expired codes from memory (if any are cached).
    This is mainly for logging and monitoring purposes.
    """
    logger.debug("Performing secure code cleanup")


def mask_contact(contact: str) -> str:
    """
    Mask contact information (email) for logging to protect PII.
    Follows the same pattern as the email service.

    Args:
        contact: Email address to mask

    Returns:
        str: Masked email address
    """
    if not contact or "@" not in contact:
        return "***@***.***"

    local, domain = contact.split("@", 1)
    if len(local) <= 2:
        masked_local = "*" * len(local)
    else:
        masked_local = local[0] + "*" * (len(local) - 2) + local[-1]

    if "." in domain:
        domain_parts = domain.split(".")
        if len(domain_parts) >= 2:
            masked_domain = domain_parts[0][:2] + "*" + "." + domain_parts[-1]
        else:
            masked_domain = "*" * len(domain)
    else:
        masked_domain = "*" * len(domain)

    return f"{masked_local}@{masked_domain}"
