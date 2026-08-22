"""
Pydantic schemas for email management API endpoints
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field, validator

from app.utils.security import (
    sanitize_filter_values,
    sanitize_input,
    validate_search_query,
    validate_uuid_or_fallback,
)


class EmailStatus(str, Enum):
    """Email status enumeration"""

    UNREAD = "unread"
    READ = "read"
    ARCHIVED = "archived"
    DELETED = "deleted"


class EmailImportance(str, Enum):
    """Email importance levels"""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class EmailAction(str, Enum):
    """Email action types"""

    MARK_READ = "mark_read"
    MARK_UNREAD = "mark_unread"
    ARCHIVE = "archive"
    DELETE = "delete"
    RESTORE = "restore"


class AttachmentSchema(BaseModel):
    """Schema for email attachments"""

    id: str
    filename: str
    content_type: str
    size_bytes: int
    download_url: Optional[str] = None
    is_inline: bool = False
    content_id: Optional[str] = None

    class Config:
        from_attributes = True


class EmailSchema(BaseModel):
    """Schema for email representation"""

    id: str
    account_id: str
    message_id: str
    thread_id: Optional[str] = None
    subject: str
    sender_email: EmailStr
    sender_name: Optional[str] = None
    recipient_emails: List[EmailStr]
    cc_emails: Optional[List[EmailStr]] = None
    bcc_emails: Optional[List[EmailStr]] = None
    body_text: Optional[str] = None
    body_html: Optional[str] = None
    status: EmailStatus
    importance: EmailImportance = EmailImportance.NORMAL
    is_starred: bool = False
    received_at: datetime
    sent_at: Optional[datetime] = None
    attachments: List[AttachmentSchema] = []
    labels: List[str] = []
    sync_cursor: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EmailListRequest(BaseModel):
    """Request schema for listing emails"""

    account_id: Optional[str] = None
    status: Optional[EmailStatus] = None
    search_query: Optional[str] = Field(None, max_length=500)
    sender_email: Optional[EmailStr] = None
    subject_contains: Optional[str] = Field(None, max_length=200)
    has_attachments: Optional[bool] = None
    is_starred: Optional[bool] = None
    importance: Optional[EmailImportance] = None
    received_after: Optional[datetime] = None
    received_before: Optional[datetime] = None
    labels: Optional[List[str]] = None
    limit: int = Field(50, ge=1, le=200)
    offset: int = Field(0, ge=0)
    sort_by: str = Field("received_at", pattern="^(received_at|sent_at|subject|sender_email)$")
    sort_order: str = Field("desc", pattern="^(asc|desc)$")

    @validator("search_query")
    def validate_search_query(cls, v):
        if v is not None:
            v = sanitize_input(v)
            if len(v.strip()) == 0:
                return None
        return v

    @validator("subject_contains")
    def validate_subject_contains(cls, v):
        if v is not None:
            v = sanitize_input(v)
            if len(v.strip()) == 0:
                return None
        return v


class EmailListResponse(BaseModel):
    """Response schema for email listing"""

    emails: List[EmailSchema]
    total_count: int
    has_more: bool
    next_offset: Optional[int] = None
    next_cursor: Optional[str] = None


class EmailDetailResponse(BaseModel):
    """Response schema for email detail"""

    email: EmailSchema
    related_emails: Optional[List[EmailSchema]] = None


class EmailActionRequest(BaseModel):
    """Request schema for email actions"""

    action: EmailAction
    email_ids: List[str] = Field(..., min_items=1, max_items=100)
    account_id: Optional[str] = None

    @validator("email_ids")
    def validate_email_ids(cls, v):
        if not v:
            raise ValueError("At least one email ID must be provided")

        for email_id in v:
            validate_uuid_or_fallback(email_id, "Email ID")

        return v


class EmailActionResponse(BaseModel):
    """Response schema for email actions"""

    action: EmailAction
    processed_count: int
    failed_count: int
    failed_email_ids: List[str] = []
    message: str


class EmailSearchRequest(BaseModel):
    """Request schema for advanced email search"""

    query: str = Field(..., min_length=1, max_length=500)
    account_ids: Optional[List[str]] = None
    search_fields: List[str] = Field(["subject", "body_text", "sender_email"], min_items=1)
    status: Optional[EmailStatus] = None
    has_attachments: Optional[bool] = None
    received_after: Optional[datetime] = None
    received_before: Optional[datetime] = None
    limit: int = Field(50, ge=1, le=200)
    offset: int = Field(0, ge=0)

    @validator("query")
    def validate_query(cls, v):
        return validate_search_query(v)

    @validator("search_fields")
    def validate_search_fields(cls, v):
        allowed_fields = ["subject", "body_text", "body_html", "sender_email", "sender_name"]
        for field in v:
            if field not in allowed_fields:
                raise ValueError(f"Invalid search field: {field}")
        return v


class EmailSearchResponse(BaseModel):
    """Response schema for email search"""

    emails: List[EmailSchema]
    total_count: int
    has_more: bool
    next_offset: Optional[int] = None
    search_query: str
    search_fields: List[str]


class AttachmentDownloadRequest(BaseModel):
    """Request schema for attachment download"""

    attachment_id: str
    email_id: str
    account_id: Optional[str] = None

    @validator("attachment_id")
    def validate_attachment_id(cls, v):
        return validate_uuid_or_fallback(v, "Attachment ID")

    @validator("email_id")
    def validate_email_id(cls, v):
        return validate_uuid_or_fallback(v, "Email ID")


class AttachmentDownloadResponse(BaseModel):
    """Response schema for attachment download"""

    download_url: str
    filename: str
    content_type: str
    size_bytes: int
    expires_at: datetime


class EmailStatsResponse(BaseModel):
    """Response schema for email statistics"""

    total_emails: int
    unread_count: int
    read_count: int
    archived_count: int
    deleted_count: int
    starred_count: int
    with_attachments_count: int
    accounts_summary: List[Dict[str, Any]]


class BulkEmailActionRequest(BaseModel):
    """Request schema for bulk email actions"""

    action: EmailAction
    filters: Dict[str, Any] = Field(..., min_items=1)
    account_id: Optional[str] = None
    dry_run: bool = False

    @validator("filters")
    def validate_filters(cls, v):
        allowed_filters = [
            "status",
            "sender_email",
            "subject_contains",
            "has_attachments",
            "is_starred",
            "importance",
            "received_after",
            "received_before",
            "labels",
        ]

        for key in v.keys():
            if key not in allowed_filters:
                raise ValueError(f"Invalid filter field: {key}")

        return sanitize_filter_values(v)


class BulkEmailActionResponse(BaseModel):
    """Response schema for bulk email actions"""

    action: EmailAction
    total_matched: int
    processed_count: int
    failed_count: int
    dry_run: bool
    message: str
