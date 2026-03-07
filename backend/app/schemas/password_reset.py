"""
Pydantic schemas for password reset functionality.
Provides secure validation and serialization for forgot/reset password requests.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, model_validator, validator

from app.utils.validation import sanitize_email_input, sanitize_password, validate_email


class ForgotPasswordRequest(BaseModel):
    """
    Schema for forgot password requests.
    """

    email: EmailStr = Field(
        ...,
        description="User's email address",
        example="user@example.com",
        min_length=5,
        max_length=320,
    )

    @validator("email")
    def validate_email_format(cls, v):
        """Validate and sanitize email input."""
        if not v:
            raise ValueError("Email is required")

        # Sanitize email input
        try:
            sanitized_email = sanitize_email_input(v)
            validated_email = validate_email(sanitized_email)
            return validated_email
        except Exception as e:
            raise ValueError(f"Invalid email format: {str(e)}")

    class Config:
        json_schema_extra = {"example": {"email": "user@example.com"}}


class ForgotPasswordResponse(BaseModel):
    """
    Schema for forgot password responses.
    Always returns success to prevent email enumeration.
    """

    status: str = Field(default="ok", description="Response status", example="ok")
    message: str = Field(
        default="If this email exists, you will receive a password reset link.",
        description="Response message",
        example="If this email exists, you will receive a password reset link.",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "status": "ok",
                "message": "If this email exists, you will receive a password reset link.",
            }
        }


class ResetPasswordRequest(BaseModel):
    """
    Schema for password reset requests.
    """

    token: str = Field(
        ...,
        description="Password reset token from email",
        example="abc123def456ghi789jkl012mno345pqr678stu901vwx234yz",
        min_length=44,
        max_length=44,
    )
    new_password: str = Field(
        ...,
        description="New password",
        example="NewSecurePassword123!",
        min_length=8,
        max_length=128,
    )
    confirm_password: str = Field(
        ...,
        description="Password confirmation",
        example="NewSecurePassword123!",
        min_length=8,
        max_length=128,
    )

    @validator("token")
    def validate_token_format(cls, v):
        """Validate reset token format."""
        if not v:
            raise ValueError("Reset token is required")

        # Check token format (URL-safe base64, 44 characters)
        if len(v) != 44:
            raise ValueError("Invalid token format")

        # Check for valid characters only
        valid_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_")
        if not all(c in valid_chars for c in v):
            raise ValueError("Invalid token format")

        return v

    @validator("new_password")
    def validate_new_password(cls, v):
        """Validate and sanitize new password."""
        if not v:
            raise ValueError("New password is required")

        # Sanitize password input
        try:
            sanitized_password = sanitize_password(v)
        except Exception as e:
            raise ValueError(f"Invalid password format: {str(e)}")

        # Basic password strength validation
        if len(sanitized_password) < 8:
            raise ValueError("Password must be at least 8 characters long")

        if len(sanitized_password) > 128:
            raise ValueError("Password must be no more than 128 characters long")

        # Check for at least 2 character categories
        has_lower = any(c.islower() for c in sanitized_password)
        has_upper = any(c.isupper() for c in sanitized_password)
        has_digit = any(c.isdigit() for c in sanitized_password)
        has_symbol = any(not c.isalnum() for c in sanitized_password)

        categories = sum([has_lower, has_upper, has_digit, has_symbol])
        if categories < 2:
            raise ValueError(
                "Password must contain at least 2 character types (uppercase, lowercase, numbers, symbols)"
            )

        return sanitized_password

    @validator("confirm_password")
    def validate_confirm_password(cls, v):
        """Validate password confirmation."""
        if not v:
            raise ValueError("Password confirmation is required")

        # Sanitize password input
        try:
            sanitized_password = sanitize_password(v)
        except Exception as e:
            raise ValueError(f"Invalid password format: {str(e)}")

        return sanitized_password

    @model_validator(mode="after")
    def passwords_match(self):
        """Ensure passwords match."""
        if (
            self.new_password
            and self.confirm_password
            and self.new_password != self.confirm_password
        ):
            raise ValueError("Passwords do not match")

        return self

    class Config:
        json_schema_extra = {
            "example": {
                "token": "abc123def456ghi789jkl012mno345pqr678stu901vwx234yz",
                "new_password": "NewSecurePassword123!",
                "confirm_password": "NewSecurePassword123!",
            }
        }


class ResetPasswordResponse(BaseModel):
    """
    Schema for password reset responses.
    """

    status: str = Field(default="ok", description="Response status", example="ok")
    message: str = Field(
        default="Password has been reset successfully. Please log in with your new password.",
        description="Response message",
        example="Password has been reset successfully. Please log in with your new password.",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "status": "ok",
                "message": "Password has been reset successfully. Please log in with your new password.",
            }
        }


class PasswordResetTokenInfo(BaseModel):
    """
    Schema for password reset token information (internal use).
    """

    id: int
    user_id: int
    expires_at: datetime
    used: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PasswordResetErrorResponse(BaseModel):
    """
    Schema for password reset error responses.
    """

    status: str = Field(default="error", description="Response status", example="error")
    message: str = Field(description="Error message", example="Invalid or expired reset token")
    error_code: Optional[str] = Field(
        default=None, description="Error code for client handling", example="INVALID_TOKEN"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "status": "error",
                "message": "Invalid or expired reset token",
                "error_code": "INVALID_TOKEN",
            }
        }


# Error codes for consistent error handling
class PasswordResetErrorCodes:
    """Error codes for password reset functionality."""

    INVALID_TOKEN = "INVALID_TOKEN"
    EXPIRED_TOKEN = "EXPIRED_TOKEN"
    TOKEN_ALREADY_USED = "TOKEN_ALREADY_USED"
    USER_NOT_FOUND = "USER_NOT_FOUND"
    EMAIL_SEND_FAILED = "EMAIL_SEND_FAILED"
    PASSWORD_TOO_WEAK = "PASSWORD_TOO_WEAK"
    PASSWORDS_DONT_MATCH = "PASSWORDS_DONT_MATCH"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
