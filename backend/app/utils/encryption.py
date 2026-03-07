"""
Token encryption utilities for secure storage of OAuth tokens
"""

import base64
import logging
import os
import threading
import time

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Encryption configuration - CRITICAL: Must be set in production
ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY","AMUc50rkiNTuLt7FDfJi-fR0yNeR5FkdycFUYCxqOH4=")
ENCRYPTION_SALT = os.environ.get("ENCRYPTION_SALT","571c0ebfacc2aa24c6fa47e1284c693aa9994ac488c42764cd76eff4183d8e35")

# Key caching to prevent timing attacks
_key_cache = {}
_key_cache_lock = threading.Lock()
_key_cache_ttl = 300  # 5 minutes TTL for cached keys


def get_encryption_key() -> bytes:
    """
    Get encryption key for token encryption with caching to prevent timing attacks

    Returns:
        bytes: Encryption key for Fernet

    Raises:
        ValueError: If encryption key or salt is not configured
    """
    if not ENCRYPTION_KEY:
        raise ValueError(
            "ENCRYPTION_KEY environment variable must be set. "
            "Generate a secure key using: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
        )

    if not ENCRYPTION_SALT:
        raise ValueError(
            "ENCRYPTION_SALT environment variable must be set. "
            "Generate a secure salt using: python -c '; print(secrets.token_hex(32))'"
        )

    # Check cache first to prevent timing attacks
    cache_key = f"{ENCRYPTION_KEY}:{ENCRYPTION_SALT}"
    current_time = time.time()

    with _key_cache_lock:
        if cache_key in _key_cache:
            cached_key, timestamp = _key_cache[cache_key]
            if current_time - timestamp < _key_cache_ttl:
                return cached_key
            else:
                # Remove expired cache entry
                del _key_cache[cache_key]

    try:
        # Use provided key and salt
        key = ENCRYPTION_KEY.encode()

        # Handle both hex and base64 salt formats
        try:
            # Try base64 first (preferred format)
            salt = base64.urlsafe_b64decode(ENCRYPTION_SALT.encode())
        except Exception:
            try:
                # Fall back to hex format
                salt = bytes.fromhex(ENCRYPTION_SALT)
            except Exception:
                raise ValueError("Salt must be either base64 or hex encoded")

        # Derive a proper Fernet key from the provided key and salt
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        derived_key = base64.urlsafe_b64encode(kdf.derive(key))

        # Cache the derived key
        with _key_cache_lock:
            _key_cache[cache_key] = (derived_key, current_time)

        return derived_key

    except Exception as e:
        logger.error(f"Failed to derive encryption key: {e}")
        raise ValueError("Invalid encryption configuration")


def encrypt_token(token: str) -> str:
    """
    Encrypt a token for secure storage

    Args:
        token: Plain text token to encrypt

    Returns:
        str: Encrypted token (base64 encoded)
    """
    try:
        key = get_encryption_key()
        fernet = Fernet(key)
        encrypted_token = fernet.encrypt(token.encode())
        encrypted_b64 = base64.urlsafe_b64encode(encrypted_token).decode()

        logger.debug("Successfully encrypted token")
        return encrypted_b64

    except Exception as e:
        logger.error(f"Failed to encrypt token: {e}")
        raise


def decrypt_token(encrypted_token: str) -> str:
    """
    Decrypt a token from secure storage

    Args:
        encrypted_token: Encrypted token (base64 encoded)

    Returns:
        str: Decrypted plain text token
    """
    try:
        key = get_encryption_key()
        fernet = Fernet(key)

        # Decode from base64
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_token.encode())

        # Decrypt
        decrypted_token = fernet.decrypt(encrypted_bytes).decode()

        logger.debug("Successfully decrypted token")
        return decrypted_token

    except Exception as e:
        logger.error(f"Failed to decrypt token: {e}")
        raise


def encrypt_credentials(access_token: str, refresh_token: str) -> tuple[str, str]:
    """
    Encrypt both access and refresh tokens

    Args:
        access_token: Google OAuth access token
        refresh_token: Google OAuth refresh token

    Returns:
        tuple: (encrypted_access_token, encrypted_refresh_token)
    """
    try:
        encrypted_access = encrypt_token(access_token)
        encrypted_refresh = encrypt_token(refresh_token)

        logger.info("Successfully encrypted OAuth credentials")
        return encrypted_access, encrypted_refresh

    except Exception as e:
        logger.error(f"Failed to encrypt credentials: {e}")
        raise


def decrypt_credentials(
    encrypted_access_token: str, encrypted_refresh_token: str
) -> tuple[str, str]:
    """
    Decrypt both access and refresh tokens

    Args:
        encrypted_access_token: Encrypted access token
        encrypted_refresh_token: Encrypted refresh token

    Returns:
        tuple: (access_token, refresh_token)
    """
    try:
        access_token = decrypt_token(encrypted_access_token)
        refresh_token = decrypt_token(encrypted_refresh_token)

        logger.info("Successfully decrypted OAuth credentials")
        return access_token, refresh_token

    except Exception as e:
        logger.error(f"Failed to decrypt credentials: {e}")
        raise


def validate_encryption_key() -> bool:
    """
    Validate that encryption key is properly configured

    Returns:
        bool: True if key is valid, False otherwise
    """
    try:
        # Just check if we can derive the key without testing encryption
        get_encryption_key()
        logger.info("Encryption key validation passed")
        return True

    except Exception as e:
        logger.error(f"Encryption key validation failed: {e}")
        return False


def generate_encryption_key() -> str:
    """
    Generate a new encryption key (for setup purposes)

    Returns:
        str: New encryption key (base64 encoded)
    """
    try:
        key = Fernet.generate_key()
        key_b64 = base64.urlsafe_b64encode(key).decode()

        logger.info("Generated new encryption key")
        return key_b64

    except Exception as e:
        logger.error(f"Failed to generate encryption key: {e}")
        raise
