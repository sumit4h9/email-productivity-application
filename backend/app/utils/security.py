"""
Security utilities for input sanitization and validation
"""

import html
import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional


def sanitize_input(value: str) -> str:
    """
    Comprehensive input sanitization to prevent XSS, SQL injection, and other attacks

    Args:
        value: Input string to sanitize

    Returns:
        Sanitized string
    """
    if not value:
        return value

    # Escape HTML entities first
    value = html.escape(value)

    # Remove SQL injection patterns
    dangerous_patterns = [
        r"(union|select|insert|update|delete|drop|create|alter|exec)",
        r'[;\'"\\]',  # SQL special characters
        r"<script|javascript:|vbscript:",  # Script injections
        r"--|\/\*|\*\/",  # SQL comments
        r"xp_|sp_",  # SQL stored procedures
        r"0x[0-9a-fA-F]+",  # Hex encoded attacks
        r"load_file|into\s+outfile|into\s+dumpfile",  # File operations
        r"benchmark|sleep|waitfor\s+delay",  # Time-based attacks
        r"information_schema|mysql\.user|pg_user",  # Database enumeration
        r"char|ascii|ord|hex|unhex",  # Character encoding attacks
        r"concat|group_concat",  # String concatenation attacks
    ]

    for pattern in dangerous_patterns:
        value = re.sub(pattern, "", value, flags=re.IGNORECASE)

    # Remove any remaining potentially dangerous characters
    value = re.sub(r'[<>"\']', "", value)

    return value.strip()


def validate_uuid_or_fallback(value: str, field_name: str = "ID") -> str:
    """
    Validate ID as UUID with fallback to strict alphanumeric validation

    Args:
        value: ID to validate
        field_name: Name of the field for error messages

    Returns:
        Validated ID

    Raises:
        ValueError: If ID format is invalid
    """
    if not value:
        raise ValueError(f"{field_name} cannot be empty")

    try:
        # Validate as UUID (most secure)
        uuid.UUID(value)
        return value
    except ValueError:
        # Fallback to strict alphanumeric + hyphen validation
        if not re.match(r"^[a-zA-Z0-9\-]{8,36}$", value):
            raise ValueError(f"Invalid {field_name} format: {value}")
        return value


def sanitize_filter_values(filters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize all string values in filter dictionary

    Args:
        filters: Dictionary of filter values

    Returns:
        Sanitized filter dictionary
    """
    sanitized_filters = {}

    for key, value in filters.items():
        if isinstance(value, str):
            sanitized_filters[key] = sanitize_input(value)
        elif isinstance(value, list):
            # Handle list values (like labels)
            sanitized_filters[key] = [
                sanitize_input(item) if isinstance(item, str) else item for item in value
            ]
        else:
            # Keep non-string values as-is
            sanitized_filters[key] = value

    return sanitized_filters


def validate_search_query(query: str) -> str:
    """
    Validate and sanitize search query

    Args:
        query: Search query to validate

    Returns:
        Sanitized search query

    Raises:
        ValueError: If query is empty after sanitization
    """
    if not query:
        raise ValueError("Search query cannot be empty")

    sanitized = sanitize_input(query)

    if not sanitized:
        raise ValueError("Search query cannot be empty after sanitization")

    return sanitized


def detect_attack_patterns(value: str) -> List[str]:
    """
    Detect potential attack patterns in input

    Args:
        value: Input to analyze

    Returns:
        List of detected attack patterns
    """
    if not value:
        return []

    attack_patterns = {
        "sql_injection": [
            r"union\s+select",
            r"insert\s+into",
            r"update\s+set",
            r"delete\s+from",
            r"drop\s+table",
            r"create\s+table",
            r"alter\s+table",
            r"exec\s*\(",
            r"xp_cmdshell",
            r"sp_executesql",
        ],
        "xss": [
            r"<script",
            r"javascript:",
            r"vbscript:",
            r"onload=",
            r"onerror=",
            r"onclick=",
            r"onmouseover=",
            r"<iframe",
            r"<object",
            r"<embed",
        ],
        "path_traversal": [r"\.\./", r"\.\.\\", r"%2e%2e%2f", r"%2e%2e%5c", r"\.\.%2f", r"\.\.%5c"],
        "command_injection": [
            r";\s*cat\s+",
            r";\s*ls\s+",
            r";\s*dir\s+",
            r";\s*type\s+",
            r"|\s*cat\s+",
            r"|\s*ls\s+",
            r"|\s*dir\s+",
            r"|\s*type\s+",
            r"`.*`",
            r"\$\(.*\)",
        ],
        "ldap_injection": [r"\(.*=.*\)", r"\(.*=.*\*\)", r"\(.*=.*\)\)", r"\(.*=.*\*\)\)"],
    }

    detected = []
    value_lower = value.lower()

    for attack_type, patterns in attack_patterns.items():
        for pattern in patterns:
            if re.search(pattern, value_lower, re.IGNORECASE):
                detected.append(attack_type)
                break

    return detected


def log_security_event(event_type: str, details: Dict[str, Any], user_id: Optional[int] = None):
    """
    Log security events for monitoring and analysis

    Args:
        event_type: Type of security event
        details: Event details
        user_id: User ID if available
    """
    import logging

    logger = logging.getLogger("security")

    log_data = {
        "event_type": event_type,
        "user_id": user_id,
        "details": details,
        "timestamp": str(datetime.utcnow()),
    }

    logger.warning(f"Security event: {log_data}")


def is_safe_filename(filename: str) -> bool:
    """
    Check if filename is safe (no path traversal, no dangerous extensions)

    Args:
        filename: Filename to check

    Returns:
        True if filename is safe, False otherwise
    """
    if not filename:
        return False

    # Check for path traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        return False

    # Check for dangerous extensions
    dangerous_extensions = [
        ".exe",
        ".bat",
        ".cmd",
        ".com",
        ".pif",
        ".scr",
        ".vbs",
        ".js",
        ".jar",
        ".php",
        ".asp",
        ".aspx",
        ".jsp",
        ".py",
        ".pl",
        ".sh",
    ]

    filename_lower = filename.lower()
    for ext in dangerous_extensions:
        if filename_lower.endswith(ext):
            return False

    # Check filename length
    if len(filename) > 255:
        return False

    return True
