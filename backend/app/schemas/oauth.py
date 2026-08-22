"""
Pydantic schemas for OAuth API requests and responses
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field


class OAuthUrlResponse(BaseModel):
    """Response schema for OAuth URL generation"""

    authorization_url: str = Field(..., description="Google OAuth authorization URL")


class OAuthCallbackRequest(BaseModel):
    """Request schema for OAuth callback"""

    code: str = Field(
        ..., min_length=4, max_length=200, description="Authorization code from Google"
    )


class ConnectedAccountResponse(BaseModel):
    """Response schema for connected account information"""

    id: str = Field(..., description="Account ID")
    provider: str = Field(..., description="OAuth provider (google, outlook, apple)")
    account_email: EmailStr = Field(..., description="Connected email address")
    last_synced_at: Optional[datetime] = Field(None, description="Last sync timestamp")
    sync_status: str = Field(..., description="Current sync status")
    is_active: bool = Field(..., description="Whether account is active")
    created_at: datetime = Field(..., description="Account creation timestamp")


class AccountListResponse(BaseModel):
    """Response schema for account list"""

    accounts: List[ConnectedAccountResponse] = Field(..., description="List of connected accounts")


class SyncTriggerResponse(BaseModel):
    """Response schema for sync trigger"""

    account_id: str = Field(..., description="Account ID")
    task_id: str = Field(..., description="Celery task ID")
    status: str = Field(..., description="Sync status")
    message: str = Field(..., description="Status message")


class AccountStatusResponse(BaseModel):
    """Response schema for detailed account status"""

    id: str = Field(..., description="Account ID")
    provider: str = Field(..., description="OAuth provider")
    account_email: EmailStr = Field(..., description="Connected email address")
    sync_status: str = Field(..., description="Current sync status")
    last_synced_at: Optional[datetime] = Field(None, description="Last sync timestamp")
    is_active: bool = Field(..., description="Whether account is active")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class OAuthCallbackResponse(BaseModel):
    """Response schema for OAuth callback"""

    account_id: str = Field(..., description="Connected account ID")
    provider: str = Field(..., description="OAuth provider")
    account_email: EmailStr = Field(..., description="Connected email address")
    status: str = Field(..., description="Connection status")
    sync_task_id: str = Field(..., description="Initial sync task ID")
    message: str = Field(..., description="Status message")


class DisconnectResponse(BaseModel):
    """Response schema for account disconnection"""

    message: str = Field(..., description="Success message")


class ErrorResponse(BaseModel):
    """Response schema for errors"""

    detail: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")


class SyncProgressResponse(BaseModel):
    """Response schema for sync progress"""

    task_id: str = Field(..., description="Task ID")
    status: str = Field(..., description="Task status")
    progress: Optional[Dict[str, Any]] = Field(None, description="Progress information")
    result: Optional[Dict[str, Any]] = Field(None, description="Task result")
    error: Optional[str] = Field(None, description="Error message if failed")
