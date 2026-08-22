"""
Comprehensive input validation utilities for security and data integrity.
"""

import math
import re
import unicodedata
from typing import Dict, List
from urllib.parse import urlparse

from email_validator import EmailNotValidError  # type: ignore
from email_validator import validate_email as validate_email_lib  # type: ignore

# from zxcvbn import zxcvbn  # type: ignore


class ValidationError(Exception):
    """Custom validation error."""

    pass


def sanitize_string(value: str, max_length: int = 1000) -> str:
    """Sanitize input string to prevent XSS and injection attacks."""
    if not isinstance(value, str):
        raise ValidationError("Input must be a string")

    value = value.strip()

    if len(value) > max_length:
        raise ValidationError(f"Input too long (max {max_length} characters)")

    # Check for dangerous patterns that could execute code
    dangerous_patterns = [
        r"(?i)<script[^>]*>.*?</script>",
        r"(?i)javascript\s*:",
        r"(?i)vbscript\s*:",
        r"(?i)data\s*:",
        r"(?i)on\w+\s*=",  # onload, onclick, etc.
        r"(?i)expression\s*\(",
        r"(?i)url\s*\(",
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, value):
            raise ValidationError("Potentially dangerous input detected")

    return value


def sanitize_general_input(value: str, field_name: str = "input", max_length: int = 1000) -> str:
    """
    Comprehensive sanitization for all general input fields (names, emails, etc.).
    This function provides enterprise-grade security for user inputs.
    """
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string")

    value = value.strip()

    if len(value) > max_length:
        raise ValidationError(f"{field_name} is too long (max {max_length} characters)")

    # Remove null bytes and control characters
    value = value.replace("\x00", "")
    value = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", value)

    # Normalize unicode to prevent homograph attacks
    value = unicodedata.normalize("NFKC", value)

    # Check for dangerous patterns
    dangerous_patterns = [
        # XSS patterns
        r"<script[^>]*>.*?</script>",
        r"javascript\s*:",
        r"vbscript\s*:",
        r"data\s*:",
        r"on\w+\s*=",
        r"expression\s*\(",
        r"url\s*\(",
        # SQL injection patterns
        r"'\s*OR\s*'1'='1",
        r"'\s*OR\s*1=1",
        r"'\s*--",
        r"'\s*;",
        r"'\s*DROP\s+TABLE",
        r"'\s*UNION\s+SELECT",
        r"'\s*EXEC\s+xp_cmdshell",
        r"\)\s*OR\s*\(",
        r"\)\s*DROP\s+TABLE",
        r"\)\s*;",
        # Command injection patterns
        r"`.*`",
        r"\$\{.*\}",
        r"\\$\(.*\)",
        # Other dangerous patterns
        r"<iframe",
        r"<svg\s+onload",
        r"<body\s+onload",
        # Hidden/invisible characters
        r"[\u200E\u200F\u202A-\u202E\u2066-\u2069]",
        # Unicode quote characters (homograph attacks)
        r"[％＇＂]",
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, value, re.IGNORECASE):
            raise ValidationError(f"{field_name} contains potentially dangerous patterns")

    return value


def sanitize_email_input(value: str) -> str:
    """
    Enhanced email sanitization with security checks.
    """
    # First apply general sanitization
    value = sanitize_general_input(value, "email", 320)

    # Additional email-specific checks
    if value.count("@") != 1:
        raise ValidationError("Email must contain exactly one @ symbol")

    if value.startswith("@") or value.endswith("@"):
        raise ValidationError("Email cannot start or end with @")

    # Check for suspicious patterns in email
    suspicious_patterns = [
        r"\.\.",  # Double dots
        r"\.@",  # Dot before @
        r"@\.",  # @ before dot
        r"\.{3,}",  # Multiple consecutive dots
    ]

    for pattern in suspicious_patterns:
        if re.search(pattern, value):
            raise ValidationError("Email contains invalid patterns")

    return value


def sanitize_name_input(value: str) -> str:
    """
    Enhanced name sanitization with security checks.
    """
    # Apply general sanitization
    value = sanitize_general_input(value, "name", 100)

    # Check for suspicious patterns in names
    suspicious_patterns = [
        r"<[^>]*>",  # HTML tags
        r"javascript\s*:",  # JavaScript
        r"data\s*:",  # Data URLs
        r"on\w+\s*=",  # Event handlers
        r"expression\s*\(",  # CSS expressions
        r"url\s*\(",  # CSS URLs
        r"\\",  # Backslashes
        r"\/",  # Forward slashes
        r"`",  # Backticks
        r"\$\{",  # Template literals
        r"<script",  # Script tags
        r"<iframe",  # Iframe tags
        r"<object",  # Object tags
        r"<embed",  # Embed tags
        # Additional SQL injection patterns for names
        r"'\s*OR\s*'1'='1",  # Single quote SQL injection
        r"'\s*OR\s*1=1",  # Single quote SQL injection
        r"'\s*--",  # Single quote comment
        r"'\s*;",  # Single quote semicolon
        r"\"\s*OR\s*\"\"=\"",  # Double quote SQL injection
        r"\"\s*OR\s*1=1",  # Double quote SQL injection
        r"\"\s*--",  # Double quote comment
        r"\"\s*;",  # Double quote semicolon
        r"DROP\s+TABLE",  # DROP TABLE
        r"UNION\s+SELECT",  # UNION SELECT
        r"EXEC\s+xp_cmdshell",  # EXEC command
    ]

    for pattern in suspicious_patterns:
        if re.search(pattern, value, re.IGNORECASE):
            raise ValidationError("Name contains potentially dangerous patterns")

    return value


def sanitize_textarea_input(value: str, max_length: int = 5000) -> str:
    """
    Enhanced textarea sanitization for longer text inputs.
    """
    # Apply general sanitization with higher length limit
    value = sanitize_general_input(value, "text", max_length)

    # Additional checks for longer text
    if value.count("<") > 10 or value.count(">") > 10:
        raise ValidationError("Text contains too many HTML-like characters")

    # Check for script injection attempts
    script_patterns = [
        r"<script[^>]*>",
        r"<\/script>",
        r"javascript\s*:",
        r"vbscript\s*:",
        r"data\s*:",
        r"on\w+\s*=",
    ]

    for pattern in script_patterns:
        if re.search(pattern, value, re.IGNORECASE):
            raise ValidationError("Text contains potentially dangerous script patterns")

    return value


def sanitize_select_input(value: str, allowed_values: list) -> str:
    """
    Sanitize select/option inputs by validating against allowed values.
    """
    if not isinstance(value, str):
        raise ValidationError("Selection must be a string")

    value = value.strip()

    # Check if value is in allowed list
    if value not in allowed_values:
        raise ValidationError(f"Invalid selection. Allowed values: {', '.join(allowed_values)}")

    return value


def validate_email(email: str) -> str:
    """Validate email address using email-validator library."""
    if not email or not isinstance(email, str):
        raise ValidationError("Email is required")

    email = email.strip()

    if len(email) > 320:  # RFC 5321 limit
        raise ValidationError("Email address is too long")

    try:
        # Use email-validator library for comprehensive validation
        validated_email = validate_email_lib(email, check_deliverability=False)
        return validated_email.normalized
    except EmailNotValidError as e:
        raise ValidationError(f"Invalid email format: {str(e)}")


def sanitize_password(password: str) -> str:
    """
    Sanitize password input to prevent injection attacks while allowing special characters.
    This function ensures the password is safe to store and process without affecting user choice.

    Security features:
    - Removes dangerous control characters and null bytes
    - Normalizes unicode to prevent homograph attacks
    - Detects and blocks potential attack patterns
    - Validates length limits to prevent DoS attacks
    - Handles edge cases and malformed input
    """
    # Enhanced input validation
    if password is None:
        raise ValidationError("Password cannot be None")

    if not isinstance(password, str):
        raise ValidationError("Password must be a string")

    # Handle empty password
    if not password:
        raise ValidationError("Password cannot be empty")

    # Check for extremely long passwords that could cause DoS
    if len(password) > 1000:
        raise ValidationError("Password is too long (max 1000 characters)")

    # Store original length for validation
    original_length = len(password)

    # Remove null bytes and control characters that could cause issues
    # More comprehensive control character removal
    password = password.replace("\x00", "")  # Remove null bytes
    password = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", password)  # Remove control chars

    # Remove additional dangerous characters
    password = re.sub(r"[\x80-\x9F]", "", password)  # Remove C1 control characters
    password = password.replace("\ufeff", "")  # Remove BOM (Byte Order Mark)
    password = password.replace("\u200b", "")  # Remove zero-width space
    password = password.replace("\u200c", "")  # Remove zero-width non-joiner
    password = password.replace("\u200d", "")  # Remove zero-width joiner
    password = password.replace("\u2060", "")  # Remove word joiner

    # Normalize unicode to prevent homograph attacks
    # Use NFKC for canonical decomposition and composition
    password = unicodedata.normalize("NFKC", password)

    # Additional security checks after normalization
    # Check for remaining dangerous patterns
    dangerous_patterns = [
        "\x00",  # Null bytes
        "\x1a",  # Substitute character
        "\ufeff",  # BOM
        "\u200b",  # Zero-width space
        "\u200c",  # Zero-width non-joiner
        "\u200d",  # Zero-width joiner
        "\u2060",  # Word joiner
    ]

    for pattern in dangerous_patterns:
        if pattern in password:
            raise ValidationError(f"Password contains invalid character: {repr(pattern)}")

    # Check for potential attack patterns
    # Look for repeated sequences that might indicate automated attacks
    if len(password) > 10:
        # Check for repeated 4+ character sequences
        for i in range(len(password) - 7):
            sequence = password[i : i + 4]
            if password.count(sequence) > 2:
                raise ValidationError("Password contains suspicious repeated patterns")

    # Check for common attack patterns
    attack_patterns = [
        r"<script",  # XSS attempts
        r"javascript:",  # JavaScript injection
        r"data:",  # Data URI injection
        r"vbscript:",  # VBScript injection
        r"on\w+\s*=",  # Event handler injection
    ]

    for pattern in attack_patterns:
        if re.search(pattern, password, re.IGNORECASE):
            raise ValidationError("Password contains potentially malicious content")

    # Validate that password still has content after sanitization
    if not password:
        raise ValidationError("Password became empty after sanitization")

    # Check if password was significantly altered (might indicate malicious input)
    if len(password) < original_length * 0.5:
        raise ValidationError("Password contained too many invalid characters")

    # Final length validation
    if len(password) > 1000:
        raise ValidationError("Password is too long after sanitization (max 1000 characters)")

    return password


def validate_password(password: str, user_inputs=None) -> dict:
    """
    Production-grade password validator.
    Returns dict with keys: ok, strength, score, entropy_bits, warnings, suggestions.
    """
    if user_inputs is None:
        user_inputs = []

    suggestions = []
    warnings = []

    # First sanitize the password to make it safe for processing
    try:
        password = sanitize_password(password)
    except ValidationError as e:
        return {
            "ok": False,
            "strength": "invalid",
            "score": 0,
            "entropy_bits": 0.0,
            "warnings": [str(e)],
            "suggestions": ["Please use a valid password format"],
        }

    # -------- Normalize --------
    pw_raw = password or ""
    pw = unicodedata.normalize("NFKC", pw_raw)
    if not pw:
        return {
            "ok": False,
            "strength": "invalid",
            "score": 0,
            "entropy_bits": 0.0,
            "warnings": ["Password is required."],
            "suggestions": ["Enter a password."],
        }

    # -------- Basic length --------
    length = len(pw)
    if length < 8:
        suggestions.append("Use at least 8 characters.")
    elif length < 16:
        suggestions.append("Consider 16+ characters for stronger protection.")

    # -------- Category checks --------
    lower = any(c.islower() for c in pw)
    upper = any(c.isupper() for c in pw)
    digit = any(c.isdigit() for c in pw)
    symbol = any(not c.isalnum() for c in pw)

    categories = sum([lower, upper, digit, symbol])
    if categories < 2:  # Lowered from 3 to 2 for 8-char passwords
        suggestions.append(
            "Use a mix of at least 2 types: uppercase, lowercase, numbers, or symbols."
        )

    # -------- Entropy (Shannon) --------
    freq = {}
    for c in pw:
        freq[c] = freq.get(c, 0) + 1
    H = 0.0
    for count in freq.values():
        p = count / length
        H -= p * math.log2(p)
    entropy_bits = H * length

    # -------- Pattern checks --------
    if re.search(r"(.)\1{3,}", pw):
        suggestions.append("Avoid repeated characters (e.g., 'aaaa').")
    if re.search(r"(?:0123|1234|2345|3456|4567|5678|6789)", pw):
        suggestions.append("Avoid sequential numbers.")
    if re.search(r"(?:abcd|qwer|asdf|zxcv)", pw.lower()):
        suggestions.append("Avoid keyboard sequences.")
    if re.fullmatch(r"(19|20)\d{2}[-/\.]?(0[1-9]|1[0-2])[-/\.]?(0[1-9]|[12]\d|3[01])", pw):
        suggestions.append("Avoid dates in your password.")

    # -------- User input leakage --------
    pw_lower = pw.lower()
    for ui in user_inputs:
        if ui and isinstance(ui, str):
            ui_norm = unicodedata.normalize("NFKC", ui).lower()
            tokens = re.split(r"[^a-z0-9]+", ui_norm)
            for token in [ui_norm] + [t for t in tokens if len(t) >= 4]:
                if token and token in pw_lower:
                    suggestions.append("Avoid using your personal information.")
                    break

    # -------- Score & strength --------
    score = 0
    if length >= 8:
        score += 1
    if categories >= 2:  # Lowered from 3 to 2 for 8-char passwords
        score += 1
    if entropy_bits >= 25:  # Lowered from 30 to be more reasonable for 8-char passwords
        score += 1
    if length >= 12:  # Bonus for longer passwords
        score += 1

    levels = ["very weak", "weak", "medium", "strong", "very strong"]
    strength = levels[min(score, 4)]

    return {
        "ok": score >= 2,  # Lowered from 3 to be more reasonable
        "strength": strength,
        "score": score,
        "entropy_bits": round(entropy_bits, 2),
        "warnings": warnings,
        "suggestions": suggestions,
    }


def validate_token_format(token: str) -> str:
    """Validate JWT token format."""
    if not token or not isinstance(token, str):
        raise ValidationError("Token is required")

    # Basic JWT format validation (3 parts separated by dots)
    parts = token.split(".")
    if len(parts) != 3:
        raise ValidationError("Invalid token format")

    return token


def validate_cors_origin(
    origin: str,
    allowed_origins: List[str],
    *,
    enforce_scheme: bool = True,
    enforce_https: bool = False,
) -> bool:
    """Securely validate CORS origin against allowed origins (scheme/host/port aware).
    - enforce_scheme: require origin scheme to match allowed scheme.
    - enforce_https: reject any http origin regardless of allow list.
    """
    if not origin:
        return False

    try:
        parsed_origin = urlparse(origin)
        if not parsed_origin.scheme or not parsed_origin.netloc:
            return False
        origin_scheme = parsed_origin.scheme.lower()
        origin_host = (parsed_origin.hostname or "").lower()
        origin_port = parsed_origin.port or (443 if origin_scheme == "https" else 80)
    except Exception:
        return False

    if enforce_https and origin_scheme != "https":
        return False

    for allowed in allowed_origins:
        if allowed == "*":
            # Only allow wildcard if not enforcing https OR origin is https
            if not enforce_https or origin_scheme == "https":
                return True
            continue

        try:
            parsed_allowed = urlparse(allowed)
            if not parsed_allowed.scheme or not parsed_allowed.netloc:
                continue
            allowed_scheme = parsed_allowed.scheme.lower()
            allowed_host = (parsed_allowed.hostname or "").lower()
            allowed_port = parsed_allowed.port or (443 if allowed_scheme == "https" else 80)
        except Exception:
            continue

        if enforce_scheme and origin_scheme != allowed_scheme:
            continue

        # exact host + port match
        if origin_host == allowed_host and origin_port == allowed_port:
            return True

        # subdomain match for "*.domain.com" (scheme/port must still match)
        if allowed_host.startswith("*.") and origin_host.endswith(allowed_host[1:]):
            if origin_port == allowed_port:
                return True

    return False


# --- Robust JWT validation/decoding helper ---
try:
    import jwt  # type: ignore
    from jwt import ExpiredSignatureError, InvalidTokenError  # type: ignore
except Exception:  # pragma: no cover
    jwt = None
    InvalidTokenError = Exception  # type: ignore
    ExpiredSignatureError = Exception  # type: ignore


def escape_sql_like_pattern(value: str) -> str:
    """
    Escape special characters in SQL LIKE patterns to prevent injection.
    This is used when searching/filtering user input in database queries.
    """
    if not isinstance(value, str):
        return ""

    # Escape SQL LIKE special characters: % _ [ ] ^
    escaped = (
        value.replace("%", "\\%")
        .replace("_", "\\_")
        .replace("[", "\\[")
        .replace("]", "\\]")
        .replace("^", "\\^")
    )
    return escaped


def escape_html_entities(value: str) -> str:
    """
    Escape HTML entities to prevent XSS when displaying user input.
    This should be used when rendering user input in HTML templates.
    """
    if not isinstance(value, str):
        return ""

    html_escapes = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#x27;",
    }

    for char, escape in html_escapes.items():
        value = value.replace(char, escape)

    return value


def safe_log_value(value: str, max_length: int = 100) -> str:
    """
    Safely prepare a value for logging by truncating and escaping dangerous characters.
    This prevents log injection attacks while preserving useful information.
    """
    if not isinstance(value, str):
        return str(value)

    # Truncate very long values
    if len(value) > max_length:
        value = value[:max_length] + "..."

    # Remove control characters and null bytes
    value = re.sub(r"[\x00-\x1F\x7F]", "", value)

    # Escape newlines and other problematic characters
    value = value.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")

    return value


def validate_and_decode_token(
    token: str,
    secret: str,
    algorithms: List[str] = ["HS256"],
    audience: str = "my-service",
    issuer: str = "https://my-auth-server.com",
) -> Dict:
    """Validate and decode a JWT token securely, enforcing standard claims."""
    if not token or not isinstance(token, str):
        raise ValidationError("Token is required")
    if not secret or not isinstance(secret, str):
        raise ValidationError("Secret is required")
    if jwt is None:
        raise ValidationError("JWT library not available")

    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=algorithms,
            audience=audience,
            issuer=issuer,
            options={"require": ["exp", "iat", "sub", "aud", "iss"]},
            leeway=30,
        )
        return payload
    except ExpiredSignatureError:
        raise ValidationError("Token has expired")
    except InvalidTokenError:
        raise ValidationError("Invalid token")
