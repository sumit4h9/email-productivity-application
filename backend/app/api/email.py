"""
Email management API endpoints for listing, searching, and managing emails
"""

import base64
import html
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.security import HTTPBearer
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import and_, asc, desc, func, or_
from sqlalchemy.orm import Session, joinedload

from app.core.storage import get_attachment_download_url, get_attachment_info
from app.db.session import get_db
from app.middleware.auth import get_current_user
from app.models.attachment import Attachment
from app.models.connected_account import ConnectedAccount
from app.models.email import Email
from app.models.user import User
from app.schemas.email import (
    AttachmentSchema,
    EmailAction,
    EmailActionRequest,
    EmailActionResponse,
    EmailDetailResponse,
    EmailListResponse,
    EmailSchema,
    EmailStatsResponse,
    EmailStatus,
)

logger = logging.getLogger(__name__)
security = HTTPBearer()

# Rate limiter setup
limiter = Limiter(key_func=get_remote_address)


def sanitize_search_query(query: str) -> str:
    """
    Sanitize search query to prevent injection attacks and improve performance

    Args:
        query: Raw search query from user input

    Returns:
        Sanitized and optimized search query
    """
    if not query or not isinstance(query, str):
        return ""

    # HTML escape to prevent XSS
    query = html.escape(query)

    # Remove special SQL characters and dangerous patterns
    dangerous_patterns = [
        r'[;\'"\\]',  # SQL special characters
        r"(union|select|insert|update|delete|drop|create|alter|exec)",  # SQL keywords
        r"<script|javascript:|vbscript:",  # Script injections
        r"[^\w\s@.-]",  # Keep only alphanumeric, spaces, @, ., and -
    ]

    for pattern in dangerous_patterns:
        query = re.sub(pattern, "", query, flags=re.IGNORECASE)

    # Limit length to prevent resource exhaustion
    query = query.strip()[:200]

    # Remove multiple spaces and normalize
    query = re.sub(r"\s+", " ", query)

    return query


def optimize_search_query(query: str) -> Dict[str, Any]:
    """
    Optimize search query for better performance and user experience

    Args:
        query: Sanitized search query

    Returns:
        Dictionary with optimized search parameters
    """
    if not query:
        return {"original": "", "terms": [], "exact_phrases": [], "exclude_terms": []}

    # Split into terms
    terms = query.lower().split()

    # Identify exact phrases (quoted strings)
    exact_phrases = []
    exclude_terms = []
    include_terms = []

    i = 0
    while i < len(terms):
        term = terms[i]

        if term.startswith('"') and term.endswith('"'):
            # Single word exact phrase
            exact_phrases.append(term[1:-1])
        elif term.startswith('"'):
            # Multi-word exact phrase
            phrase_parts = [term[1:]]
            i += 1
            while i < len(terms) and not terms[i].endswith('"'):
                phrase_parts.append(terms[i])
                i += 1
            if i < len(terms):
                phrase_parts.append(terms[i][:-1])
                exact_phrases.append(" ".join(phrase_parts))
        elif term.startswith("-"):
            # Exclude term
            exclude_terms.append(term[1:])
        else:
            # Include term
            include_terms.append(term)

        i += 1

    return {
        "original": query,
        "terms": include_terms,
        "exact_phrases": exact_phrases,
        "exclude_terms": exclude_terms,
        "has_exact_phrases": len(exact_phrases) > 0,
        "has_exclude_terms": len(exclude_terms) > 0,
    }


def build_optimized_search_conditions(optimized_query: Dict[str, Any]) -> List:
    """
    Build optimized SQLAlchemy search conditions based on query analysis

    Args:
        optimized_query: Optimized query dictionary from optimize_search_query

    Returns:
        List of SQLAlchemy conditions for efficient searching
    """
    conditions = []

    # Handle exact phrases (most specific, highest priority)
    for phrase in optimized_query["exact_phrases"]:
        phrase_conditions = [
            func.lower(Email.subject).contains(func.lower(phrase)),
            func.lower(Email.body_text).contains(func.lower(phrase)),
            func.lower(Email.sender_email).contains(func.lower(phrase)),
        ]
        conditions.append(or_(*phrase_conditions))

    # Handle include terms (medium priority)
    if optimized_query["terms"]:
        term_conditions = []
        for term in optimized_query["terms"]:
            term_conditions.extend(
                [
                    func.lower(Email.subject).contains(func.lower(term)),
                    func.lower(Email.body_text).contains(func.lower(term)),
                    func.lower(Email.sender_email).contains(func.lower(term)),
                ]
            )
        conditions.append(or_(*term_conditions))

    # Handle exclude terms (negative conditions)
    exclude_conditions = []
    for term in optimized_query["exclude_terms"]:
        exclude_conditions.extend(
            [
                ~func.lower(Email.subject).contains(func.lower(term)),
                ~func.lower(Email.body_text).contains(func.lower(term)),
                ~func.lower(Email.sender_email).contains(func.lower(term)),
            ]
        )

    if exclude_conditions:
        conditions.append(and_(*exclude_conditions))

    return conditions


router = APIRouter(prefix="/emails", tags=["Emails"])


@router.get("/search", response_model=EmailListResponse)
@limiter.limit("50/minute")  # Lower limit for search to prevent abuse
async def search_emails(
    request: Request,
    q: str = Query(
        ...,
        min_length=1,
        max_length=500,
        description="Search query (supports exact phrases with quotes, exclude terms with -)",
    ),
    account_id: Optional[str] = Query(None, description="Filter by account ID"),
    status: Optional[EmailStatus] = Query(None, description="Filter by email status"),
    limit: int = Query(20, ge=1, le=100, description="Number of emails to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EmailListResponse:
    """
    Optimized search endpoint for email content

    Supports advanced search features:
    - Exact phrases: "exact phrase"
    - Exclude terms: -unwanted
    - Multiple terms: term1 term2

    Returns:
        EmailListResponse containing search results
    """
    try:
        # Get user's account IDs once to avoid repeated subqueries
        user_account_ids = _get_user_account_ids(current_user.id, db)

        if not user_account_ids:
            return EmailListResponse(emails=[], total_count=0, has_more=False, next_offset=None)

        # Sanitize and optimize the search query
        sanitized_query = sanitize_search_query(q)
        if not sanitized_query:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid search query"
            )

        optimized_query = optimize_search_query(sanitized_query)
        search_conditions = build_optimized_search_conditions(optimized_query)

        if not search_conditions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="No valid search terms found"
            )

        # Build base filters
        filters = [Email.account_id.in_(user_account_ids)]

        if account_id:
            filters.append(Email.account_id == account_id)

        if status:
            filters.append(Email.status == status.value)

        # Build optimized query
        query = db.query(Email).filter(and_(*filters))

        # Apply search conditions
        query = query.filter(and_(*search_conditions))

        # Get total count efficiently
        try:
            total_count = query.with_entities(func.count(Email.id)).scalar()
        except Exception:
            logger.warning("Search count failed, using fallback")
            total_count = query.count()

        # Apply sorting and limit with eager loading
        query = query.order_by(desc(Email.received_at))
        emails = query.options(joinedload(Email.attachments)).limit(limit + 1).all()

        # Convert to schema objects
        email_schemas = []
        for email in emails[:limit]:  # Take only the requested limit
            attachment_schemas = [
                AttachmentSchema(
                    id=att.id,
                    filename=att.filename,
                    content_type=att.content_type,
                    size_bytes=att.size_bytes,
                    is_inline=att.is_inline,
                    content_id=att.content_id,
                )
                for att in email.attachments
            ]

            email_schema = EmailSchema(
                id=email.id,
                account_id=email.account_id,
                provider_message_id=email.provider_message_id,
                thread_id=email.thread_id,
                subject=email.subject,
                sender=email.sender,
                recipients=email.recipients,
                snippet=email.snippet,
                date=email.date,
                body_text=email.body_text,
                is_read=email.is_read,
                is_flagged=email.is_flagged,
                is_archived=email.is_archived,
                is_deleted=email.is_deleted,
                attachments=attachment_schemas,
            )
            email_schemas.append(email_schema)

        # Determine if there are more results
        has_more = len(emails) > limit

        # Log search metrics for monitoring
        logger.info(
            f"Search completed: query='{sanitized_query[:50]}...', "
            f"results={len(email_schemas)}, total={total_count}, "
            f"user={current_user.id}"
        )

        return EmailListResponse(
            emails=email_schemas,
            total_count=total_count,
            has_more=has_more,
            next_offset=None,  # Cursor-based pagination not implemented for search yet
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search failed for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Search failed"
        )


def _encode_cursor(received_at: datetime, email_id: str) -> str:
    """
    Encode pagination cursor from email data

    Args:
        received_at: Email received timestamp
        email_id: Email ID

    Returns:
        Base64 encoded cursor string
    """
    cursor_data = {"received_at": received_at.isoformat(), "email_id": email_id}
    cursor_json = json.dumps(cursor_data)
    return base64.urlsafe_b64encode(cursor_json.encode()).decode()


def _decode_cursor(cursor: str) -> tuple[datetime, str]:
    """
    Decode pagination cursor to email data

    Args:
        cursor: Base64 encoded cursor string

    Returns:
        Tuple of (received_at, email_id)

    Raises:
        HTTPException: If cursor is invalid
    """
    try:
        cursor_json = base64.urlsafe_b64decode(cursor.encode()).decode()
        cursor_data = json.loads(cursor_json)
        received_at = datetime.fromisoformat(cursor_data["received_at"])
        email_id = cursor_data["email_id"]
        return received_at, email_id
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid pagination cursor"
        )


def _get_user_account_ids(user_id: int, db: Session) -> List[str]:
    """
    Get user's active account IDs to avoid repeated subqueries

    Args:
        user_id: ID of the user
        db: Database session

    Returns:
        List of account IDs
    """
    accounts = (
        db.query(ConnectedAccount.id)
        .filter(ConnectedAccount.user_id == user_id, ConnectedAccount.is_active.is_(True))
        .all()
    )
    return [acc.id for acc in accounts]


def _validate_account_access(account_id: str, user_id: int, db: Session) -> ConnectedAccount:
    """
    Validate that the user has access to the specified account

    Args:
        account_id: ID of the account to validate
        user_id: ID of the user requesting access
        db: Database session

    Returns:
        ConnectedAccount: The validated account

    Raises:
        HTTPException: If account not found or access denied
    """
    if not account_id or len(account_id) != 36:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid account ID format"
        )

    account = (
        db.query(ConnectedAccount)
        .filter(
            ConnectedAccount.id == account_id,
            ConnectedAccount.user_id == user_id,
            ConnectedAccount.is_active.is_(True),
        )
        .first()
    )

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Account not found or access denied"
        )

    return account


def _build_email_query_filters(
    db: Session,
    user_account_ids: List[str],
    account_id: Optional[str] = None,
    status: Optional[EmailStatus] = None,
    sender_email: Optional[str] = None,
    subject_contains: Optional[str] = None,
    has_attachments: Optional[bool] = None,
    is_starred: Optional[bool] = None,
    importance: Optional[str] = None,
    received_after: Optional[datetime] = None,
    received_before: Optional[datetime] = None,
    labels: Optional[List[str]] = None,
) -> List:
    """
    Build SQLAlchemy query filters for email listing

    Args:
        db: Database session
        user_account_ids: Pre-fetched list of user's account IDs
        ... other filter parameters

    Returns:
        List of SQLAlchemy filter conditions
    """
    filters = []

    # Base filter: user's accounts only (using cached IDs)
    filters.append(Email.account_id.in_(user_account_ids))

    # Account-specific filter
    if account_id:
        if account_id not in user_account_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Account not found or access denied"
            )
        filters.append(Email.account_id == account_id)

    # Status filter
    if status:
        filters.append(Email.status == status.value)

    # Sender email filter (secure with SQLAlchemy functions)
    if sender_email:
        filters.append(func.lower(Email.sender_email).contains(func.lower(sender_email)))

    # Subject contains filter (secure with SQLAlchemy functions)
    if subject_contains:
        filters.append(func.lower(Email.subject).contains(func.lower(subject_contains)))

    # Attachments filter
    if has_attachments is not None:
        if has_attachments:
            # Emails with attachments
            attachment_subquery = db.query(Attachment.email_id).distinct().subquery()
            filters.append(Email.id.in_(attachment_subquery))
        else:
            # Emails without attachments
            attachment_subquery = db.query(Attachment.email_id).distinct().subquery()
            filters.append(~Email.id.in_(attachment_subquery))

    # Starred filter
    if is_starred is not None:
        filters.append(Email.is_starred == is_starred)

    # Importance filter
    if importance:
        filters.append(Email.importance == importance)

    # Date range filters
    if received_after:
        filters.append(Email.received_at >= received_after)

    if received_before:
        filters.append(Email.received_at <= received_before)

    # Labels filter
    if labels:
        # For now, we'll implement a simple contains check
        # In a full implementation, you might want a proper label system
        label_conditions = []
        for label in labels:
            label_conditions.append(Email.labels.contains([label]))
        filters.append(or_(*label_conditions))

    return filters


@router.get("/", response_model=EmailListResponse)
@limiter.limit("100/minute")
async def list_emails(
    request: Request,
    account_id: Optional[str] = Query(None, description="Filter by account ID"),
    status: Optional[EmailStatus] = Query(None, description="Filter by email status"),
    search_query: Optional[str] = Query(
        None,
        max_length=500,
        description="Search in subject, body, and sender (supports exact phrases with quotes, exclude terms with -)",
    ),
    sender_email: Optional[str] = Query(
        None, pattern=r"^[a-zA-Z0-9\@\.\-_]+$", description="Filter by sender email"
    ),
    subject_contains: Optional[str] = Query(
        None,
        max_length=200,
        pattern=r"^[a-zA-Z0-9\s\@\.\-_]+$",
        description="Filter by subject content",
    ),
    has_attachments: Optional[bool] = Query(None, description="Filter by attachment presence"),
    is_starred: Optional[bool] = Query(None, description="Filter by starred status"),
    importance: Optional[str] = Query(None, description="Filter by importance level"),
    received_after: Optional[datetime] = Query(
        None, description="Filter emails received after this date"
    ),
    received_before: Optional[datetime] = Query(
        None, description="Filter emails received before this date"
    ),
    labels: Optional[str] = Query(None, description="Comma-separated list of labels"),
    limit: int = Query(50, ge=1, le=200, description="Number of emails to return"),
    offset: Optional[int] = Query(
        None, ge=0, description="Number of emails to skip (legacy pagination)"
    ),
    cursor: Optional[str] = Query(None, description="Pagination cursor for efficient pagination"),
    sort_by: str = Query(
        "received_at",
        pattern="^(received_at|sent_at|subject|sender_email)$",
        description="Field to sort by",
    ),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EmailListResponse:
    """
    List emails with filtering and pagination

    Returns:
        EmailListResponse containing filtered emails and pagination info
    """
    try:
        # Get user's account IDs once to avoid repeated subqueries
        user_account_ids = _get_user_account_ids(current_user.id, db)

        if not user_account_ids:
            # User has no active accounts
            return EmailListResponse(emails=[], total_count=0, has_more=False, next_offset=None)

        # Parse labels if provided
        label_list = None
        if labels:
            label_list = [label.strip() for label in labels.split(",") if label.strip()]

        # Build query filters with cached account IDs
        filters = _build_email_query_filters(
            db=db,
            user_account_ids=user_account_ids,
            account_id=account_id,
            status=status,
            sender_email=sender_email,
            subject_contains=subject_contains,
            has_attachments=has_attachments,
            is_starred=is_starred,
            importance=importance,
            received_after=received_after,
            received_before=received_before,
            labels=label_list,
        )

        # Base query
        query = db.query(Email).filter(and_(*filters))

        # Apply optimized search query if provided
        if search_query:
            # Sanitize and optimize the search query
            sanitized_query = sanitize_search_query(search_query)
            if sanitized_query:
                optimized_query = optimize_search_query(sanitized_query)
                search_conditions = build_optimized_search_conditions(optimized_query)

                if search_conditions:
                    # Apply all search conditions
                    query = query.filter(and_(*search_conditions))

                    # Log search query for monitoring (without sensitive data)
                    logger.info(
                        f"Search query processed: {len(optimized_query['terms'])} terms, "
                        f"{len(optimized_query['exact_phrases'])} exact phrases, "
                        f"{len(optimized_query['exclude_terms'])} exclude terms"
                    )

        # Get total count with optimization
        # Use efficient count method for better performance
        try:
            total_count = query.with_entities(func.count(Email.id)).scalar()
        except Exception as e:
            logger.warning(f"Optimized count failed, falling back to standard count: {e}")
            total_count = query.count()

        # Apply sorting with index optimization
        sort_column = getattr(Email, sort_by)
        if sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))

        # Apply cursor-based pagination if cursor is provided
        if cursor:
            try:
                cursor_received_at, cursor_email_id = _decode_cursor(cursor)
                if sort_order == "desc":
                    # For descending order, get emails before the cursor
                    query = query.filter(
                        or_(
                            sort_column < cursor_received_at,
                            and_(sort_column == cursor_received_at, Email.id < cursor_email_id),
                        )
                    )
                else:
                    # For ascending order, get emails after the cursor
                    query = query.filter(
                        or_(
                            sort_column > cursor_received_at,
                            and_(sort_column == cursor_received_at, Email.id > cursor_email_id),
                        )
                    )
            except HTTPException:
                raise
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid pagination cursor"
                )
        elif offset is not None:
            # Legacy offset-based pagination
            query = query.offset(offset)

        # Apply limit and eager loading to prevent N+1 queries
        emails = query.options(joinedload(Email.attachments)).limit(limit + 1).all()

        # Convert to schema objects
        email_schemas = []
        for email in emails:
            # Use eager-loaded attachments to avoid N+1 queries
            attachment_schemas = [
                AttachmentSchema(
                    id=att.id,
                    filename=att.filename,
                    content_type=att.content_type,
                    size_bytes=att.size_bytes,
                    is_inline=att.is_inline,
                    content_id=att.content_id,
                )
                for att in email.attachments
            ]

            email_schema = EmailSchema(
                id=email.id,
                account_id=email.account_id,
                message_id=email.message_id,
                thread_id=email.thread_id,
                subject=email.subject,
                sender_email=email.sender_email,
                sender_name=email.sender_name,
                recipient_emails=email.recipient_emails,
                cc_emails=email.cc_emails,
                bcc_emails=email.bcc_emails,
                body_text=email.body_text,
                body_html=email.body_html,
                status=EmailStatus(email.status),
                importance=email.importance,
                is_starred=email.is_starred,
                received_at=email.received_at,
                sent_at=email.sent_at,
                attachments=attachment_schemas,
                labels=email.labels or [],
                sync_cursor=email.sync_cursor,
                created_at=email.created_at,
                updated_at=email.updated_at,
            )
            email_schemas.append(email_schema)

        # Calculate pagination info
        has_more = len(emails) > limit
        if has_more:
            emails = emails[:limit]  # Remove the extra email used for has_more detection

        # Generate next cursor if there are more emails
        next_cursor = None
        if has_more and emails:
            last_email = emails[-1]
            next_cursor = _encode_cursor(last_email.received_at, last_email.id)

        # Legacy offset calculation for backward compatibility
        next_offset = None
        if offset is not None:
            next_offset = offset + limit if offset + limit < total_count else None

        logger.info(
            f"Listed {len(emails)} emails for user {current_user.id} (total: {total_count})"
        )

        return EmailListResponse(
            emails=email_schemas,
            total_count=total_count,
            has_more=has_more,
            next_offset=next_offset,
            next_cursor=next_cursor,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list emails for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve emails"
        )


@router.get("/{email_id}", response_model=EmailDetailResponse)
@limiter.limit("200/minute")
async def get_email_detail(
    request: Request,
    email_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EmailDetailResponse:
    """
    Get detailed information for a specific email

    Args:
        email_id: ID of the email to retrieve

    Returns:
        EmailDetailResponse containing email details and related emails
    """
    try:
        # Validate email ID format
        if not email_id or len(email_id) != 36:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email ID format"
            )

        # Get user's account IDs
        user_account_ids = _get_user_account_ids(current_user.id, db)

        if not user_account_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="No active accounts found"
            )

        email = (
            db.query(Email)
            .filter(Email.id == email_id, Email.account_id.in_(user_account_ids))
            .first()
        )

        if not email:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Email not found or access denied"
            )

        # Get attachments
        attachments = db.query(Attachment).filter(Attachment.email_id == email.id).all()
        attachment_schemas = [
            AttachmentSchema(
                id=att.id,
                filename=att.filename,
                content_type=att.content_type,
                size_bytes=att.size_bytes,
                is_inline=att.is_inline,
                content_id=att.content_id,
            )
            for att in attachments
        ]

        # Get related emails (same thread)
        related_emails = []
        if email.thread_id:
            related_emails_query = (
                db.query(Email)
                .filter(
                    Email.thread_id == email.thread_id,
                    Email.id != email.id,
                    Email.account_id.in_(user_account_ids),
                )
                .limit(10)
                .all()
            )

            related_emails = [
                EmailSchema(
                    id=rel.id,
                    account_id=rel.account_id,
                    message_id=rel.message_id,
                    thread_id=rel.thread_id,
                    subject=rel.subject,
                    sender_email=rel.sender_email,
                    sender_name=rel.sender_name,
                    recipient_emails=rel.recipient_emails,
                    cc_emails=rel.cc_emails,
                    bcc_emails=rel.bcc_emails,
                    body_text=rel.body_text,
                    body_html=rel.body_html,
                    status=EmailStatus(rel.status),
                    importance=rel.importance,
                    is_starred=rel.is_starred,
                    received_at=rel.received_at,
                    sent_at=rel.sent_at,
                    attachments=[],  # Don't load attachments for related emails
                    labels=rel.labels or [],
                    sync_cursor=rel.sync_cursor,
                    created_at=rel.created_at,
                    updated_at=rel.updated_at,
                )
                for rel in related_emails_query
            ]

        # Create email schema
        email_schema = EmailSchema(
            id=email.id,
            account_id=email.account_id,
            message_id=email.message_id,
            thread_id=email.thread_id,
            subject=email.subject,
            sender_email=email.sender_email,
            sender_name=email.sender_name,
            recipient_emails=email.recipient_emails,
            cc_emails=email.cc_emails,
            bcc_emails=email.bcc_emails,
            body_text=email.body_text,
            body_html=email.body_html,
            status=EmailStatus(email.status),
            importance=email.importance,
            is_starred=email.is_starred,
            received_at=email.received_at,
            sent_at=email.sent_at,
            attachments=attachment_schemas,
            labels=email.labels or [],
            sync_cursor=email.sync_cursor,
            created_at=email.created_at,
            updated_at=email.updated_at,
        )

        logger.info(f"Retrieved email {email_id} for user {current_user.id}")

        return EmailDetailResponse(
            email=email_schema, related_emails=related_emails if related_emails else None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get email {email_id} for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve email details",
        )


@router.post("/actions", response_model=EmailActionResponse)
@limiter.limit("50/minute")
async def perform_email_action(
    request: Request,
    action_request: EmailActionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EmailActionResponse:
    """
    Perform actions on emails (mark as read, delete, etc.)

    Args:
        action_request: Email action request containing action type and email IDs

    Returns:
        EmailActionResponse containing action results
    """
    try:
        # Validate account access if account_id is provided
        if action_request.account_id:
            _validate_account_access(action_request.account_id, current_user.id, db)

        # Get user's account IDs
        user_account_ids = _get_user_account_ids(current_user.id, db)

        if not user_account_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="No active accounts found"
            )

        # Build base query for emails
        email_query = db.query(Email).filter(
            Email.id.in_(action_request.email_ids), Email.account_id.in_(user_account_ids)
        )

        # Add account filter if specified
        if action_request.account_id:
            email_query = email_query.filter(Email.account_id == action_request.account_id)

        emails = email_query.all()

        if not emails:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No accessible emails found for the provided IDs",
            )

        processed_count = 0
        failed_email_ids = []

        # Perform the requested action
        for email in emails:
            try:
                if action_request.action == EmailAction.MARK_READ:
                    email.status = EmailStatus.READ.value
                elif action_request.action == EmailAction.MARK_UNREAD:
                    email.status = EmailStatus.UNREAD.value
                elif action_request.action == EmailAction.ARCHIVE:
                    email.status = EmailStatus.ARCHIVED.value
                elif action_request.action == EmailAction.DELETE:
                    email.status = EmailStatus.DELETED.value
                elif action_request.action == EmailAction.RESTORE:
                    email.status = EmailStatus.UNREAD.value

                email.updated_at = datetime.utcnow()
                processed_count += 1

            except Exception as e:
                logger.error(f"Failed to process email {email.id}: {e}")
                failed_email_ids.append(email.id)

        # Commit changes
        if processed_count > 0:
            db.commit()

        failed_count = len(failed_email_ids)

        logger.info(
            f"Performed {action_request.action} on {processed_count} emails for user {current_user.id}"
        )

        return EmailActionResponse(
            action=action_request.action,
            processed_count=processed_count,
            failed_count=failed_count,
            failed_email_ids=failed_email_ids,
            message=f"Successfully processed {processed_count} emails",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to perform email action for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform email action",
        )


@router.get("/stats/summary", response_model=EmailStatsResponse)
@limiter.limit("30/minute")
async def get_email_stats(
    request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> EmailStatsResponse:
    """
    Get email statistics for the current user

    Returns:
        EmailStatsResponse containing email counts and account summaries
    """
    try:
        # Get user's account IDs
        user_account_ids = _get_user_account_ids(current_user.id, db)

        if not user_account_ids:
            # User has no active accounts
            return EmailStatsResponse(
                total_emails=0,
                unread_count=0,
                read_count=0,
                archived_count=0,
                deleted_count=0,
                starred_count=0,
                with_attachments_count=0,
                accounts_summary=[],
            )

        # Single aggregation query for all counts (performance optimization)
        stats = (
            db.query(
                func.count(Email.id).label("total_emails"),
                func.sum(func.case([(Email.status == EmailStatus.UNREAD.value, 1)], else_=0)).label(
                    "unread_count"
                ),
                func.sum(func.case([(Email.status == EmailStatus.READ.value, 1)], else_=0)).label(
                    "read_count"
                ),
                func.sum(
                    func.case([(Email.status == EmailStatus.ARCHIVED.value, 1)], else_=0)
                ).label("archived_count"),
                func.sum(
                    func.case([(Email.status == EmailStatus.DELETED.value, 1)], else_=0)
                ).label("deleted_count"),
                func.sum(func.case([(Email.is_starred.is_(True), 1)], else_=0)).label(
                    "starred_count"
                ),
            )
            .filter(Email.account_id.in_(user_account_ids))
            .first()
        )

        # Count emails with attachments (separate query for complex join)
        attachment_subquery = db.query(Attachment.email_id).distinct().subquery()
        with_attachments_count = (
            db.query(Email)
            .filter(Email.account_id.in_(user_account_ids), Email.id.in_(attachment_subquery))
            .count()
        )

        # Extract counts from aggregation result
        total_emails = stats.total_emails or 0
        unread_count = stats.unread_count or 0
        read_count = stats.read_count or 0
        archived_count = stats.archived_count or 0
        deleted_count = stats.deleted_count or 0
        starred_count = stats.starred_count or 0

        # Get account summaries
        accounts = (
            db.query(ConnectedAccount)
            .filter(
                ConnectedAccount.user_id == current_user.id, ConnectedAccount.is_active.is_(True)
            )
            .all()
        )

        accounts_summary = []
        for account in accounts:
            account_email_count = db.query(Email).filter(Email.account_id == account.id).count()
            account_unread_count = (
                db.query(Email)
                .filter(Email.account_id == account.id, Email.status == EmailStatus.UNREAD.value)
                .count()
            )

            accounts_summary.append(
                {
                    "account_id": account.id,
                    "provider": account.provider,
                    "account_email": account.account_email,
                    "total_emails": account_email_count,
                    "unread_emails": account_unread_count,
                    "sync_status": account.sync_status,
                    "last_synced_at": (
                        account.last_synced_at.isoformat() if account.last_synced_at else None
                    ),
                }
            )

        logger.info(f"Retrieved email stats for user {current_user.id}")

        return EmailStatsResponse(
            total_emails=total_emails,
            unread_count=unread_count,
            read_count=read_count,
            archived_count=archived_count,
            deleted_count=deleted_count,
            starred_count=starred_count,
            with_attachments_count=with_attachments_count,
            accounts_summary=accounts_summary,
        )

    except Exception as e:
        logger.error(f"Failed to get email stats for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve email statistics",
        )


@router.get("/attachments/{attachment_id}/download")
@limiter.limit("100/minute")
async def download_attachment(
    request: Request,
    attachment_id: str,
    expires_in: int = Query(
        3600, ge=300, le=86400, description="URL expiration time in seconds (5min-24hrs)"
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate a presigned download URL for an email attachment

    Args:
        attachment_id: ID of the attachment to download
        expires_in: URL expiration time in seconds (default: 1 hour, max: 24 hours)

    Returns:
        JSON response with download URL and metadata
    """
    try:
        # Validate attachment ID format
        if not attachment_id or len(attachment_id) != 36:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid attachment ID format"
            )
        # Get user's account IDs
        user_account_ids = _get_user_account_ids(current_user.id, db)

        if not user_account_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="No active accounts found"
            )
        # Get attachment with email and account validation
        attachment = (
            db.query(Attachment)
            .join(Email, Attachment.email_id == Email.id)
            .filter(Attachment.id == attachment_id, Email.account_id.in_(user_account_ids))
            .first()
        )

        if not attachment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attachment not found or access denied",
            )
        # Generate presigned download URL
        download_url = get_attachment_download_url(
            storage_key=attachment.storage_key, expires_in_seconds=expires_in
        )

        if not download_url:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate download URL",
            )

        # Get attachment info from storage for additional metadata
        storage_info = get_attachment_info(attachment.storage_key)

        logger.info(
            f"Generated download URL for attachment {attachment_id} "
            f"(expires in {expires_in}s) for user {current_user.id}"
        )
        return {
            "attachment_id": attachment.id,
            "filename": attachment.filename,
            "content_type": attachment.content_type,
            "size_bytes": attachment.size_bytes,
            "download_url": download_url,
            "expires_in_seconds": expires_in,
            "expires_at": (datetime.utcnow() + timedelta(seconds=expires_in)).isoformat(),
            "storage_info": storage_info,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate download URL for attachment {attachment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate download URL",
        )
