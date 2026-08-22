"""
Pydantic schemas for user session management
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UserSessionResponse(BaseModel):
    """Response schema for user session information"""

    user_id: int
    active_account_id: Optional[str] = None
    auto_sync_enabled: bool
    last_activity: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SwitchAccountRequest(BaseModel):
    """Request schema for switching active account"""

    account_id: str = Field(..., description="ID of the account to switch to")


class SwitchAccountResponse(BaseModel):
    """Response schema for account switching"""

    success: bool
    message: str
    previous_account_id: Optional[str] = None
    new_account_id: str
    auto_sync_enabled: bool
    sync_triggered: bool = Field(..., description="Whether a sync was automatically triggered")


class UserSessionStatusResponse(BaseModel):
    """Response schema for user session status"""

    has_active_account: bool
    active_account_id: Optional[str] = None
    auto_sync_enabled: bool
    connected_accounts_count: int
    last_activity: datetime


class EnableAutoSyncRequest(BaseModel):
    """Request schema for enabling auto-sync"""

    account_id: str = Field(..., description="ID of the account to enable auto-sync for")


class EnableAutoSyncResponse(BaseModel):
    """Response schema for auto-sync enablement"""

    success: bool
    message: str
    account_id: str
    auto_sync_enabled: bool
