import logging
import secrets
import time
from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status  # type: ignore
from passlib.context import CryptContext  # type: ignore
from pydantic import BaseModel, Field, field_validator, model_validator  # type: ignore
from sqlalchemy.exc import IntegrityError  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.core.jwt import (
    auto_refresh_tokens,
    create_access_token,
    create_refresh_token,
    revoke_token,
    verify_token,
)
from app.db.session import get_db
from app.middleware.auth import get_current_user
from app.middleware.rate_limit import rate_limit
from app.models.password_reset_token import PasswordResetToken
from app.models.user import User
from app.models.verification_code import VerificationCode
from app.schemas.password_reset import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
)
from app.utils.email import email_service, mask_email
from app.utils.ids import compute_user_pseudo_id
from app.utils.password_reset_tokens import (
    create_token_hash_pair,
    hash_password_secure,
    hash_reset_token,
)
from app.utils.validation import (
    ValidationError,
    sanitize_email_input,
    sanitize_general_input,
    sanitize_password,
    validate_email,
    validate_password,
)
from app.utils.verification_codes import (
    create_code_hash_pair,
    validate_code_format,
    verify_verification_code,
)

# Configure logger
logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter()


# Pydantic models for request validation
class SignupRequest(BaseModel):
    email: str = Field(..., description="User email address")
    username: str = Field(..., min_length=3, max_length=50, description="User username")
    password: str = Field(..., min_length=8, max_length=128, description="User password")

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v):
        try:
            # First apply enhanced security sanitization
            sanitized_email = sanitize_email_input(v)
            # Then validate the sanitized email
            return validate_email(sanitized_email)
        except ValidationError as e:
            raise ValueError(str(e))

    @field_validator("username")
    @classmethod
    def validate_username_format(cls, v):
        try:
            # Apply enhanced security sanitization for usernames
            return sanitize_general_input(v, "username", 50)
        except ValidationError as e:
            raise ValueError(str(e))

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v):
        try:
            # Check for XSS and code injection patterns
            dangerous_patterns = [
                # XSS patterns that could actually execute code
                r"<script[^>]*>.*?</script>",
                r"javascript\s*:",
                r"vbscript\s*:",
                r"data\s*:",
                r"on\w+\s*=",
                r"expression\s*\(",
                r"url\s*\(",
                # SQL injection patterns (single quotes)
                r"'\s*OR\s*'1'='1",
                r"'\s*OR\s*1=1",
                r"'\s*OR\s*'a'='a",
                r"'\s*--",
                r"'\s*;",
                r"'\s*DROP\s+TABLE",
                r"'\s*UNION\s+SELECT",
                r"'\s*EXEC\s+xp_cmdshell",
                r"\)\s*OR\s*\(",
                r"\)\s*DROP\s+TABLE",
                r"\)\s*;",
                # SQL injection patterns (double quotes)
                r"\"\s*OR\s*\"\"=\"",
                r"\"\s*OR\s*1=1",
                r"\"\s*--",
                r"\"\s*;",
                r"\"\s*DROP\s+TABLE",
                r"\"\s*UNION\s+SELECT",
                r"\"\s*EXEC\s+xp_cmdshell",
                # Command injection patterns
                r"`.*`",
                r"\$\{.*\}",
                r"\\$\(.*\)",
                # Block complete iframe tags that could execute (not just <iframe)
                r"<iframe[^>]*>.*?</iframe>",
                r"<iframe[^>]*\/>",
                # Block SVG with onload that could execute
                r"<svg\s+[^>]*onload[^>]*>",
                # Block body with onload that could execute
                r"<body\s+[^>]*onload[^>]*>",
                # Very long passwords (DoS protection)
                r".{100,}",
                # Hidden/invisible characters
                r"[\u200E\u200F\u202A-\u202E\u2066-\u2069]",
                # Control characters
                r"[\x00-\x1F\x7F]",
                # Unicode quote characters (homograph attacks)
                r"[％＇＂]",
                # Passwords with only spaces or very weak patterns
                r"^\s+$",
                r"^[!@#$%^&*()_+\-=\[\]{}|;:'\",.<>/?]+$",
            ]

            import re

            for pattern in dangerous_patterns:
                if re.search(pattern, v, re.IGNORECASE):
                    raise ValueError("Password contains potentially dangerous patterns")

            # Then validate password strength
            result = validate_password(v)
            if not result["ok"]:
                raise ValueError(f"Weak password: {', '.join(result['suggestions'])}")
            return v  # ✅ Return the password itself
        except ValidationError as e:
            raise ValueError(str(e))


class LoginRequest(BaseModel):
    email: Optional[str] = Field(None, description="User email address")
    username: Optional[str] = Field(None, description="User username")
    password: str = Field(..., description="User password")

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v):
        if v is None:
            return v
        try:
            # First apply enhanced security sanitization
            sanitized_email = sanitize_email_input(v)
            # Then validate the sanitized email
            return validate_email(sanitized_email)
        except ValidationError as e:
            raise ValueError(str(e))

    @field_validator("username")
    @classmethod
    def validate_username_format(cls, v):
        if v is None:
            return v
        try:
            # Apply enhanced security sanitization for usernames
            return sanitize_general_input(v, "username", 50)
        except ValidationError as e:
            raise ValueError(str(e))

    @model_validator(mode="after")
    def validate_email_or_username(self):
        if not self.email and not self.username:
            raise ValueError("Either email or username is required")
        if self.email and self.username:
            raise ValueError("Provide either email or username, not both")
        return self


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., description="Refresh token")

    @field_validator("refresh_token")
    @classmethod
    def validate_token_format(cls, v):
        try:
            # Apply general security sanitization for tokens
            return sanitize_general_input(v, "refresh token", 1000)
        except ValidationError as e:
            raise ValueError(str(e))


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


# New verification request/response models
class SignupInitRequest(BaseModel):
    email: str = Field(..., description="User email address")
    username: str = Field(..., min_length=3, max_length=50, description="User username")
    password: str = Field(..., min_length=8, max_length=128, description="User password")

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v):
        try:
            sanitized_email = sanitize_email_input(v)
            return validate_email(sanitized_email)
        except ValidationError as e:
            raise ValueError(str(e))

    @field_validator("username")
    @classmethod
    def validate_username_format(cls, v):
        try:
            return sanitize_general_input(v, "username", 50)
        except ValidationError as e:
            raise ValueError(str(e))

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v):
        try:
            sanitized_password = sanitize_password(v)
            password_validation = validate_password(sanitized_password, user_inputs=[v])
            if not password_validation["ok"]:
                raise ValueError(f"Weak password: {password_validation['suggestions']}")
            return sanitized_password
        except ValidationError as e:
            raise ValueError(str(e))


class SignupVerifyRequest(BaseModel):
    email: str = Field(..., description="User email address")
    code: str = Field(..., min_length=6, max_length=6, description="6-digit verification code")

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v):
        try:
            sanitized_email = sanitize_email_input(v)
            return validate_email(sanitized_email)
        except ValidationError as e:
            raise ValueError(str(e))

    @field_validator("code")
    @classmethod
    def validate_code_format(cls, v):
        try:
            if not validate_code_format(v):
                raise ValueError("Invalid verification code format")
            return v
        except ValidationError as e:
            raise ValueError(str(e))


class LoginInitRequest(BaseModel):
    email_or_username: str = Field(..., description="User email address or username")
    password: str = Field(..., description="User password")

    @field_validator("email_or_username")
    @classmethod
    def validate_email_or_username_format(cls, v):
        try:
            # Check if it looks like an email
            if "@" in v:
                sanitized_email = sanitize_email_input(v)
                return validate_email(sanitized_email)
            else:
                # Treat as username
                return sanitize_general_input(v, "username", 50)
        except ValidationError as e:
            raise ValueError(str(e))

    @field_validator("password")
    @classmethod
    def validate_password_format(cls, v):
        try:
            return sanitize_password(v)
        except ValidationError as e:
            raise ValueError(str(e))


class LoginVerifyRequest(BaseModel):
    email_or_username: str = Field(..., description="User email address or username")
    code: str = Field(..., min_length=6, max_length=6, description="6-digit verification code")

    @field_validator("email_or_username")
    @classmethod
    def validate_email_or_username_format(cls, v):
        try:
            if "@" in v:
                sanitized_email = sanitize_email_input(v)
                return validate_email(sanitized_email)
            else:
                return sanitize_general_input(v, "username", 50)
        except ValidationError as e:
            raise ValueError(str(e))

    @field_validator("code")
    @classmethod
    def validate_code_format(cls, v):
        try:
            if not validate_code_format(v):
                raise ValueError("Invalid verification code format")
            return v
        except ValidationError as e:
            raise ValueError(str(e))


class VerificationResponse(BaseModel):
    status: str = Field(..., description="Response status")
    contact: str = Field(..., description="Masked contact information")
    message: str = Field(..., description="Response message")


class VerificationSuccessResponse(BaseModel):
    status: str = Field(..., description="Response status")
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")


def constant_time_compare(a: str, b: str) -> bool:
    """Constant time string comparison to prevent timing attacks"""
    if len(a) != len(b):
        return False
    result = 0
    for x, y in zip(a, b):
        result |= ord(x) ^ ord(y)
    return result == 0


def sanitize_log_data(data: dict) -> dict:
    """Remove sensitive data from logs (case-insensitive, partial key matching)."""
    if not isinstance(data, dict):
        return {}

    sensitive_indicators = {
        "password",
        "pass",
        "pwd",
        "token",
        "access_token",
        "refresh_token",
        "secret",
        "client_secret",
        "api_key",
        "x-api-key",
        "key",
        "authorization",
        "cookie",
        "set-cookie",
        "email",
        "username",
        "name",
        "phone",
        "mobile",
        "ssn",
        "aadhar",
        "pan",
        "address",
    }

    def is_sensitive(k: str) -> bool:
        return k.lower() in sensitive_indicators

    sanitized = {}
    for k, v in data.items():
        if is_sensitive(str(k)):
            sanitized[k] = "[REDACTED]"
        else:
            sanitized[k] = v
    return sanitized


@router.post("/signup", response_model=TokenResponse)
async def signup(data: SignupRequest, request: Request, db: Annotated[Session, Depends(get_db)]):
    """User registration with password validation and error handling"""
    try:
        # ---- Validate and sanitize password ----
        try:
            # First sanitize the password to remove dangerous characters
            sanitized_password = sanitize_password(data.password)
            # Then validate the sanitized password
            password_validation = validate_password(
                sanitized_password, user_inputs=[data.email, data.username]
            )
            if not password_validation["ok"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "Weak password",
                        "strength": password_validation["strength"],
                        "suggestions": password_validation["suggestions"],
                    },
                )
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid password: {str(e)}"
            )

        # ---- Database transaction ----
        try:
            # Check if user already exists by email
            existing_user = db.query(User).filter(User.email.ilike(data.email.lower())).first()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
                )

            # Check if username already exists
            existing_username = (
                db.query(User).filter(User.username.ilike(data.username.lower())).first()
            )
            if existing_username:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken"
                )

            # Create user
            hashed_password = pwd_context.hash(sanitized_password)
            user = User(
                email=data.email.lower(),
                username=data.username.lower(),
                hashed_password=hashed_password,
                is_active=True,
            )

            db.add(user)
            db.commit()
            db.refresh(user)

            # Generate tokens
            access_token = create_access_token(
                {"sub": str(user.id), "jti": secrets.token_urlsafe(32)}
            )
            refresh_token = create_refresh_token(
                {"sub": str(user.id), "jti": secrets.token_urlsafe(32)}
            )

            # Log metadata only (no PII)
            log_data = sanitize_log_data(
                {
                    "request_id": getattr(request.state, "request_id", None),
                    "user_pseudo_id": compute_user_pseudo_id(user.id),
                    "password_strength": password_validation["strength"],
                }
            )
            logger.info(f"User registered successfully: {log_data}")

            return TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=30 * 60,
            )

        except IntegrityError:
            db.rollback()
            existing_user = db.query(User).filter(User.email.ilike(data.email.lower())).first()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Registration failed"
            )

    except HTTPException:
        raise
    except Exception:
        logger.error(
            "Signup error", extra={"request_id": getattr(request.state, "request_id", None)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Registration failed"
        )


@router.post("/login", response_model=TokenResponse)
@rate_limit(100, 300)  # 5 login attempts per 5 minutes per client
async def login(data: LoginRequest, request: Request, db: Annotated[Session, Depends(get_db)]):
    """User login with constant-time response"""
    try:
        # Find user by email or username
        if data.email:
            user = db.query(User).filter(User.email.ilike(data.email.lower())).first()
        else:
            user = db.query(User).filter(User.username.ilike(data.username.lower())).first()

        password_valid = False
        if user:
            password_valid = pwd_context.verify(data.password, user.hashed_password)

        if not user or not password_valid:
            time.sleep(0.1)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is inactive"
            )

        access_token = create_access_token({"sub": str(user.id), "jti": secrets.token_urlsafe(32)})
        refresh_token = create_refresh_token(
            {"sub": str(user.id), "jti": secrets.token_urlsafe(32)}
        )

        log_data = sanitize_log_data(
            {
                "request_id": getattr(request.state, "request_id", None),
                "user_pseudo_id": compute_user_pseudo_id(user.id),
            }
        )
        logger.info(f"User logged in successfully: {log_data}")

        return TokenResponse(
            access_token=access_token, refresh_token=refresh_token, expires_in=30 * 60
        )

    except HTTPException:
        raise
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        logger.error(
            "Login error", extra={"request_id": getattr(request.state, "request_id", None)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Login failed"
        )


@router.post("/refresh", response_model=TokenResponse)
@rate_limit(10, 60)  # 10 refresh attempts per minute per client
async def refresh_token(
    data: RefreshRequest, request: Request, db: Annotated[Session, Depends(get_db)]
):
    """Refresh access token with token rotation"""
    try:
        payload = verify_token(data.refresh_token, token_type="refresh")
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
            )

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type"
            )

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive"
            )

        revoke_token(data.refresh_token)

        access_token = create_access_token({"sub": str(user.id), "jti": secrets.token_urlsafe(32)})
        new_refresh_token = create_refresh_token(
            {"sub": str(user.id), "jti": secrets.token_urlsafe(32)}
        )

        log_data = sanitize_log_data(
            {
                "request_id": getattr(request.state, "request_id", None),
                "user_pseudo_id": compute_user_pseudo_id(user.id),
            }
        )
        logger.info(f"Token refreshed successfully: {log_data}")

        return TokenResponse(
            access_token=access_token, refresh_token=new_refresh_token, expires_in=30 * 60
        )

    except HTTPException:
        raise
    except Exception:
        logger.error(
            "Token refresh error", extra={"request_id": getattr(request.state, "request_id", None)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Token refresh failed"
        )


@router.post("/auto-refresh", response_model=TokenResponse)
@rate_limit(15, 60)  # 15 auto-refresh attempts per minute per client
async def auto_refresh_tokens_endpoint(
    data: RefreshRequest, request: Request, db: Annotated[Session, Depends(get_db)]
):
    """Automatic token refresh endpoint with enhanced security"""
    try:
        # Verify the refresh token first
        payload = verify_token(data.refresh_token, token_type="refresh")
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
            )

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive"
            )

        # Perform automatic token refresh
        new_access, new_refresh, error = auto_refresh_tokens(data.refresh_token, data.refresh_token)

        if error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Auto-refresh failed: {error}",
            )

        log_data = sanitize_log_data(
            {
                "request_id": getattr(request.state, "request_id", None),
                "user_pseudo_id": compute_user_pseudo_id(user.id),
            }
        )
        logger.info(f"Auto-refresh completed successfully: {log_data}")

        return TokenResponse(access_token=new_access, refresh_token=new_refresh, expires_in=30 * 60)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Auto-refresh error: {e}",
            extra={"request_id": getattr(request.state, "request_id", None)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Auto-refresh failed"
        )


@router.get("/me")
@rate_limit(100, 60)  # 100 profile retrievals per minute per client
async def get_current_user_info(current_user: Annotated[User, Depends(get_current_user)]):
    """Get current user information"""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
    }


@router.post("/logout")
@rate_limit(20, 60)  # 20 logout attempts per minute per client
async def logout(
    data: RefreshRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    request: Request,
):
    """User logout with token revocation"""
    try:
        payload = verify_token(data.refresh_token, token_type="refresh")
        if not payload or payload.get("sub") != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
            )

        revoke_token(data.refresh_token)

        log_data = sanitize_log_data(
            {
                "request_id": getattr(request.state, "request_id", None),
                "user_pseudo_id": compute_user_pseudo_id(current_user.id),
            }
        )
        logger.info(f"User logged out successfully: {log_data}")

        return {"message": "Successfully logged out"}

    except HTTPException:
        raise
    except Exception:
        logger.error(
            "Logout error", extra={"request_id": getattr(request.state, "request_id", None)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Logout failed"
        )


@router.post("/logout-all")
@rate_limit(5, 300)  # 5 logout-all attempts per 5 minutes per client
async def logout_all_devices(
    current_user: Annotated[User, Depends(get_current_user)], request: Request
):
    """Logout from all devices by revoking all user tokens"""
    try:
        log_data = sanitize_log_data(
            {
                "request_id": getattr(request.state, "request_id", None),
                "user_pseudo_id": compute_user_pseudo_id(current_user.id),
            }
        )
        logger.info(f"User logged out from all devices: {log_data}")

        return {"message": "Successfully logged out from all devices"}

    except Exception:
        logger.error(
            "Logout all devices error",
            extra={"request_id": getattr(request.state, "request_id", None)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Logout failed"
        )


@router.post("/forgot", response_model=ForgotPasswordResponse)
@rate_limit(10, 900)  # 10 requests per 15 minutes per client
async def forgot_password(
    data: ForgotPasswordRequest, request: Request, db: Annotated[Session, Depends(get_db)]
):
    """
    Send password reset email to user.
    Always returns success to prevent email enumeration attacks.
    """
    try:
        # Find user by email (case-insensitive)
        user = db.query(User).filter(User.email.ilike(data.email.lower())).first()

        if user and user.is_active:
            try:
                # Create password reset token
                plain_token, hashed_token, expires_at = create_token_hash_pair()

                # Store reset token in database
                reset_token = PasswordResetToken(
                    user_id=user.id, token=hashed_token, expires_at=expires_at, used=False
                )

                db.add(reset_token)
                db.commit()

                # Send password reset email
                email_sent = await email_service.send_password_reset_email(
                    email=user.email, reset_token=plain_token
                )

                if email_sent:
                    # Log successful request (no PII)
                    log_data = sanitize_log_data(
                        {
                            "request_id": getattr(request.state, "request_id", None),
                            "user_pseudo_id": compute_user_pseudo_id(user.id),
                            "action": "password_reset_requested",
                        }
                    )
                    logger.info(f"Password reset email sent: {log_data}")
                else:
                    # Log email failure but don't reveal to user
                    log_data = sanitize_log_data(
                        {
                            "request_id": getattr(request.state, "request_id", None),
                            "user_pseudo_id": compute_user_pseudo_id(user.id),
                            "action": "password_reset_email_failed",
                        }
                    )
                    logger.error(f"Failed to send password reset email: {log_data}")

            except Exception as e:
                # Log error but don't reveal to user
                log_data = sanitize_log_data(
                    {
                        "request_id": getattr(request.state, "request_id", None),
                        "action": "password_reset_error",
                    }
                )
                logger.error(f"Password reset token creation error: {log_data}, error: {str(e)}")

        # Always return success to prevent email enumeration
        return ForgotPasswordResponse(
            status="ok", message="If this email exists, you will receive a password reset link."
        )

    except HTTPException:
        raise
    except Exception:
        logger.error(
            "Forgot password error",
            extra={"request_id": getattr(request.state, "request_id", None)},
        )
        # Still return success to prevent information leakage
        return ForgotPasswordResponse(
            status="ok", message="If this email exists, you will receive a password reset link."
        )


@router.post("/reset", response_model=ResetPasswordResponse)
@rate_limit(5, 300)  # 5 reset attempts per 5 minutes per client
async def reset_password(
    data: ResetPasswordRequest, request: Request, db: Annotated[Session, Depends(get_db)]
):
    """
    Reset user password using reset token.
    """
    try:
        # Hash the incoming token to compare with stored hash
        hashed_token = hash_reset_token(data.token)

        # Find valid reset token by comparing hashed tokens
        reset_token = (
            db.query(PasswordResetToken)
            .filter(
                PasswordResetToken.token == hashed_token,
                PasswordResetToken.used.is_(False),
                PasswordResetToken.expires_at > datetime.utcnow(),
            )
            .first()
        )

        if not reset_token:
            # Log failed attempt
            log_data = sanitize_log_data(
                {
                    "request_id": getattr(request.state, "request_id", None),
                    "action": "password_reset_invalid_token",
                }
            )
            logger.warning(f"Invalid password reset token used: {log_data}")

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token"
            )

        # Get user
        user = db.query(User).filter(User.id == reset_token.user_id).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token"
            )

        # Hash new password
        new_hashed_password = hash_password_secure(data.new_password)

        # Update user password
        user.hashed_password = new_hashed_password
        user.updated_at = datetime.utcnow()

        # Mark token as used
        reset_token.used = True

        # Revoke all existing refresh tokens for this user (force logout from all devices)
        # This is handled by the existing JWT system

        db.commit()

        # Log successful reset
        log_data = sanitize_log_data(
            {
                "request_id": getattr(request.state, "request_id", None),
                "user_pseudo_id": compute_user_pseudo_id(user.id),
                "action": "password_reset_successful",
            }
        )
        logger.info(f"Password reset successful: {log_data}")

        return ResetPasswordResponse(
            status="ok",
            message="Password has been reset successfully. Please log in with your new password.",
        )

    except HTTPException:
        raise
    except Exception:
        logger.error(
            "Reset password error", extra={"request_id": getattr(request.state, "request_id", None)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Password reset failed"
        )


# ===== NEW VERIFICATION ENDPOINTS =====


@router.post("/signup/init", response_model=VerificationResponse)
@rate_limit(10, 3600)  # 10 signup init attempts per hour per client
async def signup_init(
    data: SignupInitRequest, request: Request, db: Annotated[Session, Depends(get_db)]
):
    """Initialize signup process with email verification"""
    try:
        # Check if user already exists by email
        existing_user = db.query(User).filter(User.email.ilike(data.email.lower())).first()
        if existing_user:
            # Return ambiguous message for security
            return VerificationResponse(
                status="pending",
                contact=mask_email(data.email),
                message="If this account doesn't exist, a verification code has been sent to your email.",
            )

        # Check if username already exists
        existing_username = (
            db.query(User).filter(User.username.ilike(data.username.lower())).first()
        )
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken"
            )

        # Create temporary user record (inactive, unverified)
        hashed_password = pwd_context.hash(data.password)
        user = User(
            email=data.email.lower(),
            username=data.username.lower(),
            hashed_password=hashed_password,
            is_active=False,  # Will be activated after verification
            email_verified=False,  # Will be verified after code verification
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        # Generate verification code
        verification_code, code_hash, expires_at = create_code_hash_pair()

        # Store verification code in database
        verification_record = VerificationCode(
            user_id=user.id,
            contact=data.email.lower(),
            purpose="signup",
            code_hash=code_hash,
            expires_at=expires_at,
            attempts=0,
            used=False,
        )

        db.add(verification_record)
        db.commit()

        # Send verification email
        email_sent = await email_service.send_verification_code_email(
            data.email, verification_code, "signup"
        )

        if not email_sent:
            logger.error(f"Failed to send verification email to {mask_email(data.email)}")
            # Don't fail the request, but log the issue

        # Log successful signup init
        log_data = sanitize_log_data(
            {
                "request_id": getattr(request.state, "request_id", None),
                "user_pseudo_id": compute_user_pseudo_id(user.id),
                "action": "signup_init_successful",
            }
        )
        logger.info(f"Signup init successful: {log_data}")

        return VerificationResponse(
            status="pending",
            contact=mask_email(data.email),
            message="If this account doesn't exist, a verification code has been sent to your email",
        )

    except HTTPException:
        raise
    except Exception:
        logger.error(
            "Signup init error", extra={"request_id": getattr(request.state, "request_id", None)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Signup initialization failed"
        )


@router.post("/signup/verify", response_model=VerificationSuccessResponse)
@rate_limit(10, 300)  # 10 signup verify attempts per 5 minutes per client
async def signup_verify(
    data: SignupVerifyRequest, request: Request, db: Annotated[Session, Depends(get_db)]
):
    """Verify signup with email verification code"""
    try:
        # Find user by email
        user = db.query(User).filter(User.email.ilike(data.email.lower())).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification request"
            )

        # Find verification code record
        verification_record = (
            db.query(VerificationCode)
            .filter(
                VerificationCode.user_id == user.id,
                VerificationCode.contact == data.email.lower(),
                VerificationCode.purpose == "signup",
                VerificationCode.used.is_(False),
                VerificationCode.expires_at > datetime.utcnow(),
            )
            .first()
        )

        if not verification_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification code",
            )

        # Check attempt limit
        if verification_record.attempts >= 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Too many verification attempts. Please request a new code.",
            )

        # Verify the code
        if not verify_verification_code(data.code, verification_record.code_hash):
            # Increment attempts
            verification_record.attempts += 1
            db.commit()

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification code"
            )

        # Mark code as used
        verification_record.used = True
        verification_record.attempts += 1

        # Activate user and mark email as verified
        user.is_active = True
        user.email_verified = True

        db.commit()

        # Generate JWT tokens
        access_token = create_access_token({"sub": str(user.id), "jti": secrets.token_urlsafe(32)})
        refresh_token = create_refresh_token(
            {"sub": str(user.id), "jti": secrets.token_urlsafe(32)}
        )

        # Log successful signup verification
        log_data = sanitize_log_data(
            {
                "request_id": getattr(request.state, "request_id", None),
                "user_pseudo_id": compute_user_pseudo_id(user.id),
                "action": "signup_verify_successful",
            }
        )
        logger.info(f"Signup verification successful: {log_data}")

        return VerificationSuccessResponse(
            status="success",
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=30 * 60,  # 30 minutes
        )

    except HTTPException:
        raise
    except Exception:
        logger.error(
            "Signup verify error", extra={"request_id": getattr(request.state, "request_id", None)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Signup verification failed"
        )


@router.post("/login/init", response_model=VerificationResponse)
@rate_limit(10, 3600)  # 5 login init attempts per hour per client
async def login_init(
    data: LoginInitRequest, request: Request, db: Annotated[Session, Depends(get_db)]
):
    """Initialize login process with email verification"""
    try:
        # Find user by email or username
        if "@" in data.email_or_username:
            user = db.query(User).filter(User.email.ilike(data.email_or_username.lower())).first()
        else:
            user = (
                db.query(User).filter(User.username.ilike(data.email_or_username.lower())).first()
            )

        # Always return the same response for security (prevent user enumeration)
        masked_contact = (
            mask_email(data.email_or_username)
            if "@" in data.email_or_username
            else data.email_or_username[:3] + "***"
        )

        if not user:
            # Return ambiguous message for security
            return VerificationResponse(
                status="pending",
                contact=masked_contact,
                message="If this account exists, a verification code has been sent to your email.",
            )

        # Verify password
        if not pwd_context.verify(data.password, user.hashed_password):
            # Return ambiguous message for security
            return VerificationResponse(
                status="pending",
                contact=masked_contact,
                message="If this account exists, a verification code has been sent to your email.",
            )

        # Check if user is active
        if not user.is_active:
            return VerificationResponse(
                status="pending",
                contact=masked_contact,
                message="If this account exists, a verification code has been sent to your email.",
            )

        # Generate verification code
        verification_code, code_hash, expires_at = create_code_hash_pair()

        # Store verification code in database
        verification_record = VerificationCode(
            user_id=user.id,
            contact=user.email,  # Always use email for verification
            purpose="login",
            code_hash=code_hash,
            expires_at=expires_at,
            attempts=0,
            used=False,
        )

        db.add(verification_record)
        db.commit()

        # Send verification email
        email_sent = await email_service.send_verification_code_email(
            user.email, verification_code, "login"
        )

        if not email_sent:
            logger.error(f"Failed to send verification email to {mask_email(user.email)}")
            # Don't fail the request, but log the issue

        # Log successful login init
        log_data = sanitize_log_data(
            {
                "request_id": getattr(request.state, "request_id", None),
                "user_pseudo_id": compute_user_pseudo_id(user.id),
                "action": "login_init_successful",
            }
        )
        logger.info(f"Login init successful: {log_data}")

        return VerificationResponse(
            status="pending",
            contact=mask_email(user.email),
            message="If this account exists, a verification code has been sent to your email.",
        )

    except HTTPException:
        raise
    except Exception:
        logger.error(
            "Login init error", extra={"request_id": getattr(request.state, "request_id", None)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Login initialization failed"
        )


@router.post("/login/verify", response_model=VerificationSuccessResponse)
@rate_limit(10, 300)  # 10 login verify attempts per 5 minutes per client
async def login_verify(
    data: LoginVerifyRequest, request: Request, db: Annotated[Session, Depends(get_db)]
):
    """Verify login with email verification code"""
    try:
        # Find user by email or username
        if "@" in data.email_or_username:
            user = db.query(User).filter(User.email.ilike(data.email_or_username.lower())).first()
        else:
            user = (
                db.query(User).filter(User.username.ilike(data.email_or_username.lower())).first()
            )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification request"
            )

        # Find verification code record
        verification_record = (
            db.query(VerificationCode)
            .filter(
                VerificationCode.user_id == user.id,
                VerificationCode.contact == user.email,
                VerificationCode.purpose == "login",
                VerificationCode.used.is_(False),
                VerificationCode.expires_at > datetime.utcnow(),
            )
            .first()
        )

        if not verification_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification code",
            )

        # Check attempt limit
        if verification_record.attempts >= 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Too many verification attempts. Please request a new code.",
            )

        # Verify the code
        if not verify_verification_code(data.code, verification_record.code_hash):
            # Increment attempts
            verification_record.attempts += 1
            db.commit()

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification code"
            )

        # Mark code as used
        verification_record.used = True
        verification_record.attempts += 1

        db.commit()

        # Generate JWT tokens
        access_token = create_access_token({"sub": str(user.id), "jti": secrets.token_urlsafe(32)})
        refresh_token = create_refresh_token(
            {"sub": str(user.id), "jti": secrets.token_urlsafe(32)}
        )

        # Log successful login verification
        log_data = sanitize_log_data(
            {
                "request_id": getattr(request.state, "request_id", None),
                "user_pseudo_id": compute_user_pseudo_id(user.id),
                "action": "login_verify_successful",
            }
        )
        logger.info(f"Login verification successful: {log_data}")

        return VerificationSuccessResponse(
            status="success",
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=30 * 60,  # 30 minutes
        )

    except HTTPException:
        raise
    except Exception:
        logger.error(
            "Login verify error", extra={"request_id": getattr(request.state, "request_id", None)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Login verification failed"
        )
