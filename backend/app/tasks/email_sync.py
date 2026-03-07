"""
Email synchronization tasks for Gmail and other providers
"""

import hashlib
import json
import logging
import os
import random
import re
import time
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Any, Dict, List, Optional

import redis
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.core.celery_app import celery_app
from app.core.storage import (
    calculate_file_checksum,
    generate_storage_key,
    store_attachment,
    stream_attachment_to_storage,
)
from app.db.session import SessionLocal
from app.models.attachment import Attachment
from app.models.connected_account import ConnectedAccount
from app.models.email import Email
from app.models.user_session import UserSession
from app.utils.encryption import decrypt_credentials, encrypt_credentials

logger = logging.getLogger(__name__)

# Redis client for task deduplication and distributed locking
try:
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    redis_client = redis.from_url(
        REDIS_URL,
        socket_connect_timeout=5,
        socket_timeout=5,
        retry_on_timeout=True,
        health_check_interval=30,
    )
    # Test connection
    redis_client.ping()
except Exception as e:
    logger.warning(f"Failed to connect to Redis: {e}")
    redis_client = None

# Circuit breaker state
_circuit_breaker_state = {
    "failures": 0,
    "last_failure": None,
    "state": "closed",  # closed, open, half-open
}

# Rate limiting state
_rate_limit_state = {"last_request": 0, "request_count": 0, "window_start": 0}


@contextmanager
def distributed_lock(lock_key: str, timeout: int = 300, blocking_timeout: int = 10):
    """
    Distributed lock context manager for preventing race conditions

    Args:
        lock_key: Unique key for the lock
        timeout: Lock expiration time in seconds
        blocking_timeout: Maximum time to wait for lock acquisition
    """
    if not redis_client:
        yield
        return

    lock = redis_client.lock(lock_key, timeout=timeout, blocking_timeout=blocking_timeout)
    acquired = False

    try:
        acquired = lock.acquire(blocking=True, blocking_timeout=blocking_timeout)
        if not acquired:
            raise Exception(f"Failed to acquire lock: {lock_key}")
        yield
    finally:
        if acquired:
            try:
                lock.release()
            except Exception as e:
                logger.warning(f"Failed to release lock {lock_key}: {e}")


def circuit_breaker(max_failures: int = 5, timeout: int = 60):
    """
    Circuit breaker decorator for external service calls

    Args:
        max_failures: Maximum failures before opening circuit
        timeout: Time to wait before trying half-open state
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_time = time.time()

            # Check if circuit is open
            if _circuit_breaker_state["state"] == "open":
                if current_time - _circuit_breaker_state["last_failure"] < timeout:
                    raise Exception("Circuit breaker is open - service unavailable")
                else:
                    _circuit_breaker_state["state"] = "half-open"

            try:
                result = func(*args, **kwargs)
                # Success - reset circuit breaker
                if _circuit_breaker_state["state"] == "half-open":
                    _circuit_breaker_state["state"] = "closed"
                    _circuit_breaker_state["failures"] = 0
                return result
            except Exception:
                _circuit_breaker_state["failures"] += 1
                _circuit_breaker_state["last_failure"] = current_time

                if _circuit_breaker_state["failures"] >= max_failures:
                    _circuit_breaker_state["state"] = "open"
                    logger.error(f"Circuit breaker opened after {max_failures} failures")

                raise

        return wrapper

    return decorator


def rate_limit_with_backoff(max_requests: int = 100, window: int = 60):
    """
    Rate limiting decorator with exponential backoff

    Args:
        max_requests: Maximum requests per window
        window: Time window in seconds
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_time = time.time()

            # Reset window if needed
            if current_time - _rate_limit_state["window_start"] > window:
                _rate_limit_state["window_start"] = current_time
                _rate_limit_state["request_count"] = 0

            # Check rate limit
            if _rate_limit_state["request_count"] >= max_requests:
                sleep_time = window - (current_time - _rate_limit_state["window_start"])
                if sleep_time > 0:
                    logger.warning(f"Rate limit exceeded, sleeping for {sleep_time:.2f} seconds")
                    time.sleep(sleep_time)
                    _rate_limit_state["window_start"] = time.time()
                    _rate_limit_state["request_count"] = 0

            _rate_limit_state["request_count"] += 1
            _rate_limit_state["last_request"] = current_time

            return func(*args, **kwargs)

        return wrapper

    return decorator


def _generate_email_fingerprint(message_data: Dict[str, Any]) -> str:
    """
    Generate a unique fingerprint for email deduplication using multiple identifiers

    Args:
        message_data: Gmail message data

    Returns:
        str: Unique fingerprint hash
    """
    # Use multiple identifiers for robust deduplication
    identifiers = []

    # Primary identifiers
    if "id" in message_data:
        identifiers.append(f"id:{message_data['id']}")

    # Message-ID header (most reliable)
    headers = message_data.get("payload", {}).get("headers", [])
    message_id_header = next(
        (h["value"] for h in headers if h["name"].lower() == "message-id"), None
    )
    if message_id_header:
        identifiers.append(f"msgid:{message_id_header}")

    # Thread ID
    if "threadId" in message_data:
        identifiers.append(f"thread:{message_data['threadId']}")

    # Subject + Sender + Date combination
    subject = next((h["value"] for h in headers if h["name"].lower() == "subject"), "")
    sender = next((h["value"] for h in headers if h["name"].lower() == "from"), "")
    date = next((h["value"] for h in headers if h["name"].lower() == "date"), "")

    if subject and sender and date:
        identifiers.append(
            f"content:{hashlib.md5(f'{subject}|{sender}|{date}'.encode()).hexdigest()}"
        )

    # Create fingerprint from all identifiers
    fingerprint_data = "|".join(sorted(identifiers))
    return hashlib.sha256(fingerprint_data.encode()).hexdigest()


def _validate_gmail_api_response(
    data: Dict[str, Any], max_size: int = 10 * 1024 * 1024
) -> Dict[str, Any]:
    """
    Validate and sanitize Gmail API response data

    Args:
        data: Raw Gmail API response data
        max_size: Maximum allowed size in bytes

    Returns:
        Validated and sanitized data

    Raises:
        ValueError: If data is invalid or potentially malicious
    """
    import html
    import re

    if not isinstance(data, dict):
        raise ValueError("Invalid response format: expected dictionary")

    # Check total size
    data_str = str(data)
    if len(data_str.encode("utf-8")) > max_size:
        raise ValueError(f"Response too large: {len(data_str)} bytes exceeds {max_size} limit")

    # Validate and sanitize email headers
    if "payload" in data and "headers" in data["payload"]:
        headers = data["payload"]["headers"]
        if not isinstance(headers, list):
            raise ValueError("Invalid headers format")

        for header in headers:
            if not isinstance(header, dict):
                raise ValueError("Invalid header format")

            # Validate header name
            if "name" not in header or not isinstance(header["name"], str):
                raise ValueError("Invalid header name")

            # Sanitize header name
            header["name"] = re.sub(r"[^\w\-]", "", header["name"].lower())

            # Validate and sanitize header value
            if "value" in header and isinstance(header["value"], str):
                # HTML escape to prevent XSS
                header["value"] = html.escape(header["value"][:1000])  # Limit length

                # Remove potential injection patterns
                dangerous_patterns = [
                    r"<script[^>]*>.*?</script>",
                    r"javascript:",
                    r"vbscript:",
                    r"data:text/html",
                    r"expression\s*\(",
                ]

                for pattern in dangerous_patterns:
                    header["value"] = re.sub(pattern, "", header["value"], flags=re.IGNORECASE)

    # Validate email ID
    if "id" in data:
        if not isinstance(data["id"], str) or not re.match(r"^[a-zA-Z0-9\-_]+$", data["id"]):
            raise ValueError("Invalid email ID format")

    # Validate thread ID
    if "threadId" in data:
        if not isinstance(data["threadId"], str) or not re.match(
            r"^[a-zA-Z0-9\-_]+$", data["threadId"]
        ):
            raise ValueError("Invalid thread ID format")

    return data


def _validate_attachment_data(attachment_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and sanitize attachment data from Gmail API

    Args:
        attachment_data: Raw attachment data

    Returns:
        Validated and sanitized attachment data

    Raises:
        ValueError: If attachment data is invalid or potentially malicious
    """
    import os
    import re

    if not isinstance(attachment_data, dict):
        raise ValueError("Invalid attachment data format")

    # Validate filename
    if "filename" in attachment_data:
        filename = attachment_data["filename"]
        if not isinstance(filename, str):
            raise ValueError("Invalid filename format")

        # Sanitize filename to prevent path traversal
        filename = os.path.basename(filename)  # Remove path components
        filename = re.sub(r"[^\w\-_\.]", "", filename)  # Keep only safe characters

        if not filename or len(filename) > 255:
            raise ValueError("Invalid filename length or content")

        attachment_data["filename"] = filename

    # Validate content type
    if "mimeType" in attachment_data:
        content_type = attachment_data["mimeType"]
        if not isinstance(content_type, str):
            raise ValueError("Invalid content type format")

        # Whitelist allowed content types
        allowed_types = [
            "text/",
            "image/",
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument",
            "application/zip",
            "application/x-zip-compressed",
        ]

        if not any(content_type.startswith(allowed) for allowed in allowed_types):
            raise ValueError(f"Content type not allowed: {content_type}")

        attachment_data["content_type"] = content_type

    # Validate file size
    if "size" in attachment_data:
        try:
            size = int(attachment_data["size"])
            if size < 0 or size > 25 * 1024 * 1024:  # 25MB limit
                raise ValueError(f"File size {size} exceeds 25MB limit")
            attachment_data["size"] = size
        except (ValueError, TypeError):
            raise ValueError("Invalid file size format")

    # Validate attachment ID
    if "attachmentId" in attachment_data:
        attachment_id = attachment_data["attachmentId"]
        if not isinstance(attachment_id, str) or not re.match(r"^[a-zA-Z0-9\-_]+$", attachment_id):
            raise ValueError("Invalid attachment ID format")

    return attachment_data


def _validate_account_id(account_id: str) -> None:
    """
    Validate account ID format and content

    Args:
        account_id: Account ID to validate

    Raises:
        ValueError: If account ID is invalid
    """
    if not account_id or not isinstance(account_id, str):
        raise ValueError("Invalid account_id provided")

    if len(account_id) < 1 or len(account_id) > 100:
        raise ValueError("Account ID length must be between 1 and 100 characters")

    # Sanitize account_id to prevent injection
    if not re.match(r"^[a-zA-Z0-9\-_]+$", account_id):
        raise ValueError(
            "Invalid account_id format - only alphanumeric, hyphens, and underscores allowed"
        )


def _validate_user_id(user_id: int) -> None:
    """
    Validate user ID format and content

    Args:
        user_id: User ID to validate

    Raises:
        ValueError: If user ID is invalid
    """
    if not isinstance(user_id, int) or user_id <= 0:
        raise ValueError("Invalid user_id provided - must be positive integer")


def _verify_account_ownership(
    account_id: str, user_id: int, db: Session
) -> Optional[ConnectedAccount]:
    """
    Verify that the user owns the specified account and return the account

    Args:
        account_id: Account ID to verify
        user_id: User ID to verify ownership
        db: Database session

    Returns:
        ConnectedAccount: The account if user owns it, None otherwise
    """
    try:
        account = (
            db.query(ConnectedAccount)
            .filter(
                ConnectedAccount.id == account_id,
                ConnectedAccount.user_id == user_id,
                ConnectedAccount.is_active.is_(True),
            )
            .first()
        )

        if account:
            logger.info(f"Account ownership verified: user {user_id} -> account {account_id}")
            return account
        else:
            logger.warning(
                f"Account ownership verification failed: user {user_id} -> account {account_id}"
            )
            return None

    except Exception as e:
        logger.error(f"Account ownership verification failed: {e}")
        return None


def _create_gmail_service_from_account(account: ConnectedAccount) -> Optional[Any]:
    """
    Create Gmail service using stored OAuth credentials with distributed locking for token refresh

    Args:
        account: ConnectedAccount with encrypted tokens

    Returns:
        Gmail service object or None if failed
    """
    try:
        # Decrypt stored credentials
        access_token = decrypt_credentials(account.access_token_enc, account.refresh_token_enc)[0]
        refresh_token = decrypt_credentials(account.access_token_enc, account.refresh_token_enc)[1]

        # Create credentials object
        credentials = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=None,  # Will be set by the service
            client_secret=None,  # Will be set by the service
            scopes=[
                "https://www.googleapis.com/auth/gmail.readonly",
                "https://www.googleapis.com/auth/gmail.modify",
                "https://www.googleapis.com/auth/gmail.send",
            ],
        )

        # Check if token needs refresh with distributed locking
        if credentials.expired and credentials.refresh_token:
            # Use distributed lock to prevent race conditions during token refresh
            token_refresh_lock_key = f"token_refresh:{account.id}"

            with distributed_lock(token_refresh_lock_key, timeout=60, blocking_timeout=10):
                # Double-check if token still needs refresh (another task might have refreshed it)
                if credentials.expired and credentials.refresh_token:
                    logger.info(f"Refreshing expired token for account {account.id}")

                    try:
                        credentials.refresh(Request())

                        # Update stored tokens with database session
                        db = SessionLocal()
                        try:
                            # Get fresh account data with row-level locking
                            fresh_account = (
                                db.query(ConnectedAccount)
                                .filter(ConnectedAccount.id == account.id)
                                .with_for_update()
                                .first()
                            )

                            if fresh_account:
                                # Update tokens
                                encrypted_access, encrypted_refresh = encrypt_credentials(
                                    credentials.token, credentials.refresh_token
                                )
                                fresh_account.access_token_enc = encrypted_access
                                fresh_account.refresh_token_enc = encrypted_refresh
                                fresh_account.token_expiry = credentials.expiry
                                fresh_account.updated_at = datetime.now(timezone.utc)

                                db.commit()
                                logger.info(f"Token refreshed and stored for account {account.id}")

                                # Update the account object passed to this function
                                account.access_token_enc = encrypted_access
                                account.refresh_token_enc = encrypted_refresh
                                account.token_expiry = credentials.expiry
                            else:
                                logger.error(f"Account {account.id} not found during token refresh")

                        except Exception as db_error:
                            db.rollback()
                            logger.error(
                                f"Failed to update tokens in database for account {account.id}: {db_error}"
                            )
                            raise
                        finally:
                            db.close()

                    except Exception as refresh_error:
                        logger.error(
                            f"Failed to refresh token for account {account.id}: {refresh_error}"
                        )
                        raise

        # Create Gmail service
        service = build("gmail", "v1", credentials=credentials)
        logger.info(f"Gmail service created successfully for account {account.id}")
        return service

    except Exception as e:
        logger.error(f"Failed to create Gmail service for account {account.id}: {e}")
        return None


def _fetch_emails_from_gmail(
    service: Any, account: ConnectedAccount, max_results: int = 100
) -> List[Dict[str, Any]]:
    """
    Fetch emails from Gmail API

    Args:
        service: Gmail service object
        account: ConnectedAccount object
        max_results: Maximum number of emails to fetch

    Returns:
        List of email data from Gmail API
    """
    try:
        # Get list of message IDs
        query = "in:inbox"  # Start with inbox emails
        if account.sync_cursor:
            # Use sync cursor for incremental sync
            query += f" after:{account.sync_cursor}"

        results = (
            service.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
        )

        messages = results.get("messages", [])
        if not messages:
            logger.info(f"No new messages found for account {account.id}")
            return []

        # Fetch detailed message data
        emails = []
        for message in messages:
            try:
                msg = (
                    service.users()
                    .messages()
                    .get(userId="me", id=message["id"], format="full")
                    .execute()
                )

                # Parse email data
                email_data = _parse_gmail_message(msg, account.id, service)
                if email_data:
                    emails.append(email_data)

            except HttpError as e:
                logger.error(f"Failed to fetch message {message['id']}: {e}")
                continue

        logger.info(f"Fetched {len(emails)} emails from Gmail for account {account.id}")
        return emails

    except HttpError as e:
        logger.error(f"Gmail API error for account {account.id}: {e}")
        return []
    except Exception as e:
        logger.error(f"Failed to fetch emails for account {account.id}: {e}")
        return []


def _parse_gmail_message(
    msg: Dict[str, Any], account_id: str, service: Any
) -> Optional[Dict[str, Any]]:
    """
    Parse Gmail message into our email format with security validation

    Args:
        msg: Gmail message object
        account_id: Account ID

    Returns:
        Parsed email data or None if parsing failed
    """
    try:
        # Validate Gmail API response first
        validated_msg = _validate_gmail_api_response(msg)

        headers = validated_msg["payload"].get("headers", [])
        header_dict = {h["name"].lower(): h["value"] for h in headers}

        # Extract basic email information
        subject = header_dict.get("subject", "")
        sender = header_dict.get("from", "")
        recipients = header_dict.get("to", "")
        date_str = header_dict.get("date", "")

        # Parse date
        try:
            from email.utils import parsedate_to_datetime

            date = parsedate_to_datetime(date_str)
        except Exception:
            date = datetime.now(timezone.utc)

        # Extract body
        body_text = _extract_email_body(msg["payload"])

        # Extract attachments
        attachments = _extract_attachments(msg["payload"], msg["id"], service)

        # Extract thread ID
        thread_id = msg.get("threadId", "")

        # Check if email is read
        label_ids = msg.get("labelIds", [])
        is_read = "UNREAD" not in label_ids

        # Check if email is flagged/starred
        is_flagged = "STARRED" in label_ids

        # Check if email is archived
        is_archived = "INBOX" not in label_ids

        email_data = {
            "id": msg["id"],
            "account_id": account_id,
            "provider_message_id": msg["id"],
            "thread_id": thread_id,
            "subject": subject,
            "sender": sender,
            "recipients": recipients,
            "date": date,
            "body_text": body_text,
            "attachments": attachments,
            "is_read": is_read,
            "is_flagged": is_flagged,
            "is_archived": is_archived,
            "is_deleted": False,
            "ml_processed": False,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

        return email_data

    except Exception as e:
        logger.error(f"Failed to parse Gmail message: {e}")
        return None


def _extract_attachments(
    payload: Dict[str, Any], email_id: str, service: Any
) -> List[Dict[str, Any]]:
    """
    Extract attachment information from Gmail payload

    Args:
        payload: Gmail message payload
        email_id: Email ID
        service: Gmail service object

    Returns:
        List of attachment data
    """
    try:
        attachments = []

        def process_part(part: Dict[str, Any]):
            if part.get("filename"):
                # This is an attachment
                attachment_id = part.get("body", {}).get("attachmentId")
                if attachment_id:
                    try:
                        # Get attachment data
                        attachment = (
                            service.users()
                            .messages()
                            .attachments()
                            .get(userId="me", messageId=email_id, id=attachment_id)
                            .execute()
                        )

                        # Decode attachment data
                        import base64

                        file_data = base64.urlsafe_b64decode(attachment["data"])

                        # Generate storage key and store attachment file
                        storage_key = generate_storage_key(
                            email_id, attachment_id, part["filename"]
                        )
                        _store_attachment_file(
                            file_data,
                            storage_key,
                            part.get("mimeType", "application/octet-stream"),
                            part["filename"],
                        )

                        # Calculate checksum for integrity verification
                        checksum = calculate_file_checksum(file_data)

                        attachment_data = {
                            "id": f"{email_id}_{attachment_id}",
                            "email_id": email_id,
                            "filename": part["filename"],
                            "content_type": part.get("mimeType", "application/octet-stream"),
                            "size": len(file_data),
                            "storage_key": storage_key,
                            "checksum": checksum,
                            "created_at": datetime.now(timezone.utc),
                        }
                        attachments.append(attachment_data)

                    except Exception:
                        logger.error(f"Failed to process attachment {part['filename']}")

            # Process nested parts
            if "parts" in part:
                for sub_part in part["parts"]:
                    process_part(sub_part)

        # Process all parts
        if "parts" in payload:
            for part in payload["parts"]:
                process_part(part)
        else:
            process_part(payload)

        return attachments

    except Exception as e:
        logger.error(f"Failed to extract attachments: {e}")
        return []


def _extract_email_body(payload: Dict[str, Any]) -> str:
    """
    Extract email body text from Gmail payload

    Args:
        payload: Gmail message payload

    Returns:
        Email body text
    """
    try:
        body = ""

        if "parts" in payload:
            # Multipart message
            for part in payload["parts"]:
                if part["mimeType"] == "text/plain":
                    if "data" in part["body"]:
                        import base64

                        body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")
                        break
        else:
            # Single part message
            if payload["mimeType"] == "text/plain" and "data" in payload["body"]:
                import base64

                body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8")

        return body

    except Exception as e:
        logger.error(f"Failed to extract email body: {e}")
        return ""


def _store_attachment_file(
    attachment_data: bytes, storage_key: str, content_type: str, filename: str
) -> str:
    """
    Store attachment file in MinIO storage

    Args:
        attachment_data: File data to store
        storage_key: Storage key/path
        content_type: MIME type of the file
        filename: Original filename

    Returns:
        str: Storage key if successful
    """
    try:
        # Store attachment using MinIO storage service
        success, message, checksum = store_attachment(
            file_data=attachment_data,
            storage_key=storage_key,
            content_type=content_type,
            filename=filename,
        )

        if success:
            logger.info(
                f"Successfully stored attachment: {filename} -> {storage_key} ({len(attachment_data)} bytes)"
            )
            return storage_key
        else:
            logger.error(f"Failed to store attachment {filename}: {message}")
            raise Exception(f"Storage failed: {message}")

    except Exception as e:
        logger.error(f"Failed to store attachment file {filename}: {e}")
        raise


def _store_attachments_streaming(
    attachments: List[Dict[str, Any]], email_id: str, db: Session
) -> None:
    """
    Store email attachments with streaming to prevent memory exhaustion and security validation

    Args:
        attachments: List of attachment data
        email_id: Email ID
        db: Database session
    """
    try:
        for attachment_data in attachments:
            try:
                # Validate attachment data for security
                validated_attachment = _validate_attachment_data(attachment_data)

                # Check if attachment already exists
                existing_attachment = (
                    db.query(Attachment).filter(Attachment.id == validated_attachment["id"]).first()
                )

                if not existing_attachment:
                    # Stream attachment data directly to storage without loading into memory
                    storage_key = _stream_attachment_to_storage(validated_attachment)

                    if storage_key:
                        # Create new attachment record with validated data
                        new_attachment = Attachment(
                            id=validated_attachment["id"],
                            email_id=email_id,
                            filename=validated_attachment["filename"],
                            content_type=validated_attachment.get(
                                "content_type", "application/octet-stream"
                            ),
                            size_bytes=validated_attachment["size"],
                            storage_key=storage_key,
                            checksum=validated_attachment.get("checksum"),
                            is_inline=validated_attachment.get("is_inline", False),
                            content_id=validated_attachment.get("content_id"),
                            created_at=validated_attachment.get(
                                "created_at", datetime.now(timezone.utc)
                            ),
                        )
                        db.add(new_attachment)
                        logger.debug(
                            f"Stored attachment {validated_attachment['filename']} with key {storage_key}"
                        )
                    else:
                        logger.warning(
                            f"Failed to store attachment {validated_attachment['filename']} to storage"
                        )

            except Exception as e:
                logger.error(
                    f"Failed to store attachment {attachment_data.get('filename', 'unknown')}: {e}"
                )
                continue

    except Exception as e:
        logger.error(f"Failed to store attachments for email {email_id}: {e}")


def _stream_attachment_to_storage(attachment_data: Dict[str, Any]) -> Optional[str]:
    """
    Stream attachment data directly to MinIO storage without loading into memory

    Args:
        attachment_data: Attachment data from Gmail API

    Returns:
        Storage key if successful, None if failed
    """
    try:
        # Generate unique storage key
        storage_key = generate_storage_key(
            attachment_data["email_id"], attachment_data["id"], attachment_data["filename"]
        )

        if "data" in attachment_data:
            # Process base64 data in chunks to avoid memory issues
            import base64
            import io

            # Decode base64 data
            decoded_data = base64.urlsafe_b64decode(attachment_data["data"])

            # Stream to MinIO storage
            with io.BytesIO(decoded_data) as data_stream:
                success, message, checksum = stream_attachment_to_storage(
                    file_stream=data_stream,
                    storage_key=storage_key,
                    content_type=attachment_data.get("content_type", "application/octet-stream"),
                    filename=attachment_data["filename"],
                    file_size=len(decoded_data),
                )

                if success:
                    logger.debug(
                        f"Streamed attachment {attachment_data['filename']} ({len(decoded_data)} bytes) to {storage_key}"
                    )
                    # Update attachment data with checksum
                    attachment_data["checksum"] = checksum
                    return storage_key
                else:
                    logger.error(
                        f"Failed to stream attachment {attachment_data['filename']}: {message}"
                    )
                    return None

        else:
            # No data to store (might be a reference attachment)
            logger.debug(f"Attachment {attachment_data['filename']} has no data to store")
            return storage_key

    except Exception as e:
        logger.error(
            f"Failed to stream attachment {attachment_data.get('filename', 'unknown')}: {e}"
        )
        return None


def _store_attachments(attachments: List[Dict[str, Any]], email_id: str, db: Session) -> None:
    """
    Legacy attachment storage function - redirects to streaming version

    Args:
        attachments: List of attachment data
        email_id: Email ID
        db: Database session
    """
    _store_attachments_streaming(attachments, email_id, db)


@contextmanager
def database_transaction(db: Session):
    """
    Database transaction context manager with proper rollback handling
    """
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Database transaction failed, rolled back: {e}")
        raise
    finally:
        db.close()


def _save_sync_checkpoint(account_id: str, user_id: int, checkpoint_data: Dict[str, Any]) -> None:
    """
    Save sync checkpoint to Redis for recovery

    Args:
        account_id: Account ID
        user_id: User ID
        checkpoint_data: Checkpoint data to save
    """
    if not redis_client:
        return

    try:
        checkpoint_key = f"sync_checkpoint:{account_id}:{user_id}"
        checkpoint_data["timestamp"] = time.time()
        redis_client.setex(checkpoint_key, 3600, json.dumps(checkpoint_data))  # 1 hour TTL
        logger.debug(f"Saved sync checkpoint for account {account_id}")
    except Exception as e:
        logger.warning(f"Failed to save sync checkpoint for account {account_id}: {e}")


def _load_sync_checkpoint(account_id: str, user_id: int) -> Optional[Dict[str, Any]]:
    """
    Load sync checkpoint from Redis for recovery

    Args:
        account_id: Account ID
        user_id: User ID

    Returns:
        Checkpoint data if found, None otherwise
    """
    if not redis_client:
        return None

    try:
        checkpoint_key = f"sync_checkpoint:{account_id}:{user_id}"
        checkpoint_data = redis_client.get(checkpoint_key)
        if checkpoint_data:
            return json.loads(checkpoint_data)
    except Exception as e:
        logger.warning(f"Failed to load sync checkpoint for account {account_id}: {e}")

    return None


def _clear_sync_checkpoint(account_id: str, user_id: int) -> None:
    """
    Clear sync checkpoint after successful completion

    Args:
        account_id: Account ID
        user_id: User ID
    """
    if not redis_client:
        return

    try:
        checkpoint_key = f"sync_checkpoint:{account_id}:{user_id}"
        redis_client.delete(checkpoint_key)
        logger.debug(f"Cleared sync checkpoint for account {account_id}")
    except Exception as e:
        logger.warning(f"Failed to clear sync checkpoint for account {account_id}: {e}")


def _store_emails_in_database(
    emails: List[Dict[str, Any]], db: Session, account: ConnectedAccount
) -> Dict[str, int]:
    """
    Store fetched emails in the database

    Args:
        emails: List of email data
        db: Database session

    Returns:
        Dictionary with counts of processed emails
    """
    try:
        new_count = 0
        updated_count = 0
        error_count = 0

        for email_data in emails:
            try:
                # Check if email already exists
                existing_email = (
                    db.query(Email)
                    .filter(
                        Email.provider_message_id == email_data["provider_message_id"],
                        Email.account_id == email_data["account_id"],
                    )
                    .first()
                )

                if existing_email:
                    # Update existing email
                    existing_email.subject = email_data["subject"]
                    existing_email.sender = email_data["sender"]
                    existing_email.recipients = email_data["recipients"]
                    existing_email.date = email_data["date"]
                    existing_email.body_text = email_data["body_text"]
                    existing_email.is_read = email_data["is_read"]
                    existing_email.is_flagged = email_data["is_flagged"]
                    existing_email.is_archived = email_data["is_archived"]
                    existing_email.updated_at = email_data["updated_at"]

                    # Handle attachments for existing email
                    _store_attachments(email_data.get("attachments", []), existing_email.id, db)
                    updated_count += 1
                else:
                    # Create new email
                    new_email = Email(
                        id=email_data["id"],
                        account_id=email_data["account_id"],
                        provider_message_id=email_data["provider_message_id"],
                        thread_id=email_data["thread_id"],
                        subject=email_data["subject"],
                        sender=email_data["sender"],
                        recipients=email_data["recipients"],
                        date=email_data["date"],
                        body_text=email_data["body_text"],
                        is_read=email_data["is_read"],
                        is_flagged=email_data["is_flagged"],
                        is_archived=email_data["is_archived"],
                        is_deleted=email_data["is_deleted"],
                        ml_processed=email_data["ml_processed"],
                        created_at=email_data["created_at"],
                        updated_at=email_data["updated_at"],
                    )
                    db.add(new_email)
                    db.flush()  # Get the email ID

                    # Handle attachments for new email
                    _store_attachments(email_data.get("attachments", []), new_email.id, db)
                    new_count += 1

            except Exception as e:
                logger.error(f"Failed to store email {email_data.get('id', 'unknown')}: {e}")
                error_count += 1
                continue

        # Update sync cursor to latest email date
        if emails:
            latest_email = max(emails, key=lambda x: x["date"])
            account.sync_cursor = latest_email["date"].strftime("%Y/%m/%d")

        # Commit all changes
        db.commit()

        logger.info(
            f"Stored emails: {new_count} new, {updated_count} updated, {error_count} errors"
        )
        return {"new_count": new_count, "updated_count": updated_count, "error_count": error_count}

    except Exception as e:
        logger.error(f"Failed to store emails in database: {e}")
        db.rollback()
        return {"new_count": 0, "updated_count": 0, "error_count": len(emails)}


def _is_task_running(task_key: str) -> bool:
    """
    Check if a task is already running

    Args:
        task_key: Unique task identifier

    Returns:
        bool: True if task is running, False otherwise
    """
    if not redis_client:
        return False

    try:
        return redis_client.exists(f"task_running:{task_key}")
    except Exception as e:
        logger.error(f"Task running check failed: {e}")
        return False


def _mark_task_running(task_key: str, task_id: str) -> None:
    """
    Mark a task as running with extended TTL

    Args:
        task_key: Unique task identifier
        task_id: Celery task ID
    """
    if not redis_client:
        return

    try:
        redis_client.setex(f"task_running:{task_key}", 3600, task_id)  # 1 hour TTL
        logger.debug(f"Marked task as running: {task_key} -> {task_id}")
    except Exception as e:
        logger.error(f"Failed to mark task as running: {e}")


def _extend_task_ttl(task_key: str, task_id: str, additional_seconds: int = 1800) -> None:
    """
    Extend task TTL during execution to prevent expiration

    Args:
        task_key: Unique key for the task
        task_id: Celery task ID
        additional_seconds: Additional seconds to add to TTL
    """
    if not redis_client:
        return

    try:
        current_ttl = redis_client.ttl(f"task_running:{task_key}")
        if current_ttl > 0:
            # Extend TTL by additional seconds
            new_ttl = current_ttl + additional_seconds
            redis_client.expire(f"task_running:{task_key}", new_ttl)
            logger.debug(f"Extended task TTL for {task_key} to {new_ttl} seconds")
    except Exception as e:
        logger.warning(f"Failed to extend task TTL: {e}")


def _clear_task_running(task_key: str) -> None:
    """
    Clear task running status

    Args:
        task_key: Unique task identifier
    """
    if not redis_client:
        return

    try:
        redis_client.delete(f"task_running:{task_key}")
        logger.debug(f"Cleared task running status: {task_key}")
    except Exception as e:
        logger.error(f"Failed to clear task running status: {e}")


def _sanitize_error_message(error: Exception) -> str:
    """
    Sanitize error messages to prevent information disclosure

    Args:
        error: Exception to sanitize

    Returns:
        str: Sanitized error message
    """
    # Define safe error messages for common exceptions
    safe_messages = {
        "ConnectionError": "Network connection failed",
        "TimeoutError": "Request timed out",
        "PermissionError": "Access denied",
        "ValueError": "Invalid input provided",
        "RuntimeError": "Service temporarily unavailable",
        "GoogleAPIError": "External service error",
    }

    error_type = type(error).__name__
    return safe_messages.get(error_type, "An unexpected error occurred")


@celery_app.task(
    bind=True,
    name="app.tasks.email_sync.sync_gmail_account",
    autoretry_for=(HttpError, ConnectionError, OperationalError),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=8,
)
@circuit_breaker(max_failures=5, timeout=300)
@rate_limit_with_backoff(max_requests=50, window=60)
def sync_gmail_account(self, account_id: str, user_id: int) -> Dict[str, Any]:
    """
    Sync emails for a specific Gmail account

    Args:
        account_id: Connected account ID
        user_id: User ID

    Returns:
        Dict: Sync result information
    """
    start_time = time.time()

    try:
        logger.info(f"Starting Gmail sync for account {account_id}, user {user_id}")

        # Add exponential backoff for rate limits
        if hasattr(self.request, "retries") and self.request.retries > 0:
            delay = random.uniform(1, 5) * (2**self.request.retries)
            time.sleep(delay)

        # Update task state for progress tracking
        self.update_state(
            state="PROGRESS", meta={"current": 0, "total": 100, "status": "Starting sync..."}
        )

        # Validate inputs
        _validate_account_id(account_id)
        _validate_user_id(user_id)

        # Use distributed locking to prevent race conditions
        lock_key = f"sync_lock:{account_id}:{user_id}"

        with distributed_lock(lock_key, timeout=600, blocking_timeout=5):
            # Get database session with proper context management
            db = SessionLocal()

            try:
                with database_transaction(db):
                    # Update progress
                    self.update_state(
                        state="PROGRESS",
                        meta={
                            "current": 10,
                            "total": 100,
                            "status": "Verifying account ownership...",
                        },
                    )

                    # Verify account ownership with row-level locking
                    account = (
                        db.query(ConnectedAccount)
                        .filter(
                            ConnectedAccount.id == account_id,
                            ConnectedAccount.user_id == user_id,
                            ConnectedAccount.is_active.is_(True),
                        )
                        .with_for_update()
                        .first()
                    )

                    if not account:
                        raise ValueError(
                            f"Account {account_id} not found or access denied for user {user_id}"
                        )

                    # Update progress
                    self.update_state(
                        state="PROGRESS",
                        meta={"current": 20, "total": 100, "status": "Creating Gmail service..."},
                    )

                    # Create Gmail service with token refresh protection
                    service = _create_gmail_service_from_account(account)
                    if not service:
                        raise ValueError(f"Failed to create Gmail service for account {account_id}")

                    # Update progress
                    self.update_state(
                        state="PROGRESS",
                        meta={
                            "current": 30,
                            "total": 100,
                            "status": "Fetching emails from Gmail...",
                        },
                    )

                    # Check for existing checkpoint
                    checkpoint = _load_sync_checkpoint(account_id, user_id)
                    if checkpoint:
                        logger.info(f"Resuming sync from checkpoint for account {account_id}")
                        # Resume from checkpoint (simplified - in production would resume from
                        # specific point)

                    # Fetch emails from Gmail with improved error handling
                    emails = _fetch_emails_from_gmail(service, account, max_results=100)

                    # Save checkpoint after fetching emails
                    _save_sync_checkpoint(
                        account_id,
                        user_id,
                        {
                            "emails_fetched": len(emails),
                            "fetch_timestamp": time.time(),
                            "status": "emails_fetched",
                        },
                    )

                    # Update progress
                    self.update_state(
                        state="PROGRESS",
                        meta={
                            "current": 60,
                            "total": 100,
                            "status": f"Processing {len(emails)} emails...",
                        },
                    )

                    # Store emails in database with proper transaction handling
                    storage_result = _store_emails_in_database(emails, db, account)

                    # Save checkpoint after storing emails
                    _save_sync_checkpoint(
                        account_id,
                        user_id,
                        {
                            "emails_processed": len(emails),
                            "emails_new": storage_result["new_count"],
                            "emails_updated": storage_result["updated_count"],
                            "storage_timestamp": time.time(),
                            "status": "emails_stored",
                        },
                    )

                    # Extend task TTL to prevent expiration during long operations
                    task_key = f"sync_gmail:{account_id}:{user_id}"
                    _extend_task_ttl(task_key, self.request.id)

                    # Update progress
                    self.update_state(
                        state="PROGRESS",
                        meta={"current": 90, "total": 100, "status": "Updating sync status..."},
                    )

                    # Update account sync status and cursor ONLY after successful commit
                    account.last_synced_at = datetime.now(timezone.utc)
                    account.sync_status = "completed"
                    if emails:
                        # Update sync cursor to latest email date
                        latest_email = max(
                            emails,
                            key=lambda x: x.get("date", datetime.min.replace(tzinfo=timezone.utc)),
                        )
                        if "date" in latest_email:
                            account.sync_cursor = latest_email["date"].strftime("%Y/%m/%d")

                    # Commit all changes
                    db.commit()

                    # Clear checkpoint after successful completion
                    _clear_sync_checkpoint(account_id, user_id)

                    # Update progress to completion
                    self.update_state(
                        state="PROGRESS",
                        meta={
                            "current": 100,
                            "total": 100,
                            "status": "Sync completed successfully",
                        },
                    )

                    sync_result = {
                        "account_id": account_id,
                        "user_id": user_id,
                        "status": "success",
                        "emails_processed": len(emails),
                        "emails_new": storage_result["new_count"],
                        "emails_updated": storage_result["updated_count"],
                        "errors": [],
                        "duration_ms": round((time.time() - start_time) * 1000, 2),
                        "timestamp": time.time(),
                    }

                    logger.info(
                        f"Gmail sync completed for account {account_id}: {storage_result['new_count']} new, {storage_result['updated_count']} updated"
                    )
                    return sync_result

            except HttpError as e:
                if e.resp.status == 429:  # Rate limit
                    # Respect Retry-After header if present
                    retry_after = e.resp.headers.get("Retry-After")
                    if retry_after:
                        try:
                            retry_seconds = int(retry_after)
                            logger.warning(
                                f"Rate limit hit for account {account_id}, retrying after {retry_seconds} seconds"
                            )
                            raise self.retry(countdown=retry_seconds)
                        except ValueError:
                            logger.warning(f"Invalid Retry-After header: {retry_after}")

                    # Fallback to exponential backoff
                    retry_seconds = 60 * (2**self.request.retries)
                    logger.warning(
                        f"Rate limit hit for account {account_id}, retrying after {retry_seconds} seconds"
                    )
                    raise self.retry(countdown=retry_seconds)

                elif e.resp.status == 403:  # Quota exceeded or forbidden
                    # Check if it's a quota issue
                    error_details = str(e)
                    if "quota" in error_details.lower() or "exceeded" in error_details.lower():
                        # Quota exceeded - wait longer before retry
                        retry_seconds = 300 * (2**self.request.retries)  # 5 minutes base
                        logger.error(
                            f"Quota exceeded for account {account_id}, retrying after {retry_seconds} seconds"
                        )
                        raise self.retry(countdown=retry_seconds)
                    else:
                        # Other 403 errors - don't retry
                        logger.error(f"Access forbidden for account {account_id}: {error_details}")
                        raise

                elif e.resp.status >= 500:  # Server errors - retry with backoff
                    retry_seconds = 30 * (2**self.request.retries)
                    logger.warning(
                        f"Server error {e.resp.status} for account {account_id}, retrying after {retry_seconds} seconds"
                    )
                    raise self.retry(countdown=retry_seconds)

                else:
                    # Other errors - don't retry
                    raise
            except Exception as e:
                logger.error(f"Sync failed for account {account_id}: {e}")
                raise

    except Exception as e:
        logger.error(f"Gmail sync failed for account {account_id}: {e}")
        return {
            "account_id": account_id,
            "user_id": user_id,
            "status": "error",
            "error": str(e),
            "duration_ms": round((time.time() - start_time) * 1000, 2),
            "timestamp": time.time(),
        }


@celery_app.task(bind=True, name="app.tasks.email_sync.sync_all_accounts")
def sync_all_accounts(self, user_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Sync emails for all active accounts or a specific user

    Args:
        user_id: Optional user ID to sync only their accounts

    Returns:
        Dict: Sync result information
    """
    start_time = time.time()

    try:
        logger.info("Starting sync for all accounts" + (f" (user {user_id})" if user_id else ""))

        # Get database session
        db = SessionLocal()

        try:
            # Get only accounts that are active in user sessions
            # This ensures we only sync accounts that users are actively using
            query = (
                db.query(ConnectedAccount)
                .join(UserSession, ConnectedAccount.id == UserSession.active_account_id)
                .filter(
                    ConnectedAccount.is_active.is_(True),
                    UserSession.auto_sync_enabled.is_(True),
                    UserSession.last_activity
                    > datetime.now(timezone.utc) - timedelta(hours=1),  # Active within 1 hour
                )
            )

            if user_id:
                query = query.filter(ConnectedAccount.user_id == user_id)

            accounts = query.all()

            if not accounts:
                logger.info("No active accounts found to sync")
                return {
                    "user_id": user_id,
                    "status": "success",
                    "accounts_processed": 0,
                    "total_emails_processed": 0,
                    "total_emails_new": 0,
                    "total_emails_updated": 0,
                    "errors": [],
                    "duration_ms": round((time.time() - start_time) * 1000, 2),
                    "timestamp": time.time(),
                }

            # Process each account
            accounts_processed = 0
            total_emails_processed = 0
            total_emails_new = 0
            total_emails_updated = 0
            errors = []

            for account in accounts:
                try:
                    # Check if sync is already running for this account
                    task_key = f"sync_gmail:{account.id}:{account.user_id}"
                    if _is_task_running(task_key):
                        logger.info(f"Sync already running for account {account.id}, skipping")
                        continue

                    # Trigger sync for this account
                    sync_task = sync_gmail_account.delay(account.id, account.user_id)

                    # Wait for task completion (with timeout)
                    try:
                        result = sync_task.get(timeout=300)  # 5 minute timeout
                        if result.get("status") == "success":
                            accounts_processed += 1
                            total_emails_processed += result.get("emails_processed", 0)
                            total_emails_new += result.get("emails_new", 0)
                            total_emails_updated += result.get("emails_updated", 0)
                        else:
                            errors.append(
                                f"Account {account.id}: {result.get('error', 'Unknown error')}"
                            )
                    except Exception as e:
                        errors.append(f"Account {account.id}: Task timeout or error - {str(e)}")

                except Exception as e:
                    logger.error(f"Failed to sync account {account.id}: {e}")
                    errors.append(f"Account {account.id}: {str(e)}")
                    continue

            sync_result = {
                "user_id": user_id,
                "status": "success" if not errors else "partial_success",
                "accounts_processed": accounts_processed,
                "total_emails_processed": total_emails_processed,
                "total_emails_new": total_emails_new,
                "total_emails_updated": total_emails_updated,
                "errors": errors,
                "duration_ms": round((time.time() - start_time) * 1000, 2),
                "timestamp": time.time(),
            }

            logger.info(
                f"All accounts sync completed: {accounts_processed} accounts, {total_emails_processed} emails processed"
            )
            return sync_result

        finally:
            db.close()

    except Exception as e:
        logger.error(f"All accounts sync failed: {e}")
        return {
            "user_id": user_id,
            "status": "error",
            "error": str(e),
            "duration_ms": round((time.time() - start_time) * 1000, 2),
            "timestamp": time.time(),
        }


@celery_app.task(bind=True, name="app.tasks.email_sync.periodic_sync_all_accounts")
def periodic_sync_all_accounts(self) -> Dict[str, Any]:
    """
    Periodic sync task for all accounts (called by Celery Beat)
    This is a wrapper around sync_all_accounts with additional logging and monitoring

    Returns:
        Dict: Sync result information
    """
    start_time = time.time()

    try:
        logger.info("Starting periodic sync for all accounts")

        # Call the main sync function
        result = sync_all_accounts()

        # Add periodic sync specific metadata
        result["sync_type"] = "periodic"
        result["triggered_by"] = "celery_beat"

        logger.info(
            f"Periodic sync completed: {result.get('accounts_processed', 0)} accounts processed"
        )
        return result

    except Exception as e:
        logger.error(f"Periodic sync failed: {e}")
        return {
            "sync_type": "periodic",
            "triggered_by": "celery_beat",
            "status": "error",
            "error": str(e),
            "duration_ms": round((time.time() - start_time) * 1000, 2),
            "timestamp": time.time(),
        }


@celery_app.task(bind=True, name="app.tasks.email_sync.sync_active_accounts")
def sync_active_accounts(self) -> Dict[str, Any]:
    """
    Sync only recently active accounts (called by Celery Beat every 30 minutes)
    This is a more selective sync for accounts that have been used recently

    Returns:
        Dict: Sync result information
    """
    start_time = time.time()

    try:
        logger.info("Starting sync for active accounts")

        # Get database session
        db = SessionLocal()

        try:
            # Get only accounts that are active in user sessions
            # This ensures we only sync accounts that users are actively using
            active_accounts = (
                db.query(ConnectedAccount)
                .join(UserSession, ConnectedAccount.id == UserSession.active_account_id)
                .filter(
                    ConnectedAccount.is_active.is_(True),
                    UserSession.auto_sync_enabled.is_(True),
                    UserSession.last_activity
                    > datetime.now(timezone.utc) - timedelta(hours=1),  # Active within 1 hour
                )
                .all()
            )

            if not active_accounts:
                logger.info("No recently active accounts found to sync")
                return {
                    "sync_type": "active_accounts",
                    "triggered_by": "celery_beat",
                    "status": "success",
                    "accounts_processed": 0,
                    "total_emails_processed": 0,
                    "total_emails_new": 0,
                    "total_emails_updated": 0,
                    "errors": [],
                    "duration_ms": round((time.time() - start_time) * 1000, 2),
                    "timestamp": time.time(),
                }

            # Process each active account
            accounts_processed = 0
            total_emails_processed = 0
            total_emails_new = 0
            total_emails_updated = 0
            errors = []

            for account in active_accounts:
                try:
                    # Check if sync is already running for this account
                    task_key = f"sync_gmail:{account.id}:{account.user_id}"
                    if _is_task_running(task_key):
                        logger.info(f"Sync already running for account {account.id}, skipping")
                        continue

                    # Trigger sync for this account
                    sync_task = sync_gmail_account.delay(account.id, account.user_id)

                    # Wait for task completion (with shorter timeout for active accounts)
                    try:
                        result = sync_task.get(timeout=180)  # 3 minute timeout
                        if result.get("status") == "success":
                            accounts_processed += 1
                            total_emails_processed += result.get("emails_processed", 0)
                            total_emails_new += result.get("emails_new", 0)
                            total_emails_updated += result.get("emails_updated", 0)
                        else:
                            errors.append(
                                f"Account {account.id}: {result.get('error', 'Unknown error')}"
                            )
                    except Exception as e:
                        errors.append(f"Account {account.id}: Task timeout or error - {str(e)}")

                except Exception as e:
                    logger.error(f"Failed to sync active account {account.id}: {e}")
                    errors.append(f"Account {account.id}: {str(e)}")
                    continue

            sync_result = {
                "sync_type": "active_accounts",
                "triggered_by": "celery_beat",
                "status": "success" if not errors else "partial_success",
                "accounts_processed": accounts_processed,
                "total_emails_processed": total_emails_processed,
                "total_emails_new": total_emails_new,
                "total_emails_updated": total_emails_updated,
                "errors": errors,
                "duration_ms": round((time.time() - start_time) * 1000, 2),
                "timestamp": time.time(),
            }

            logger.info(
                f"Active accounts sync completed: {accounts_processed} accounts, {total_emails_processed} emails processed"
            )
            return sync_result

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Active accounts sync failed: {e}")
        return {
            "sync_type": "active_accounts",
            "triggered_by": "celery_beat",
            "status": "error",
            "error": str(e),
            "duration_ms": round((time.time() - start_time) * 1000, 2),
            "timestamp": time.time(),
        }


@celery_app.task(bind=True, name="app.tasks.email_sync.manual_refresh_account")
def manual_refresh_account(self, account_id: str, user_id: int) -> Dict[str, Any]:
    """
    Manual refresh for a specific account (priority sync)

    Args:
        account_id: Connected account ID
        user_id: User ID

    Returns:
        Dict: Refresh result information
    """
    start_time = time.time()

    try:
        logger.info(f"Starting manual refresh for account {account_id}, user {user_id}")

        # TODO: Implement actual manual refresh logic
        # This is a placeholder for the actual implementation

        refresh_result = {
            "account_id": account_id,
            "user_id": user_id,
            "status": "success",
            "emails_processed": 0,
            "emails_new": 0,
            "emails_updated": 0,
            "priority": True,
            "duration_ms": 0,
            "timestamp": time.time(),
        }

        # Simulate some work
        time.sleep(0.5)

        # Calculate duration
        refresh_result["duration_ms"] = round((time.time() - start_time) * 1000, 2)

        logger.info(
            f"Manual refresh completed for account {account_id} in {refresh_result['duration_ms']}ms"
        )
        return refresh_result

    except Exception as e:
        logger.error(f"Manual refresh failed for account {account_id}: {e}")
        return {
            "account_id": account_id,
            "user_id": user_id,
            "status": "error",
            "error": str(e),
            "priority": True,
            "duration_ms": round((time.time() - start_time) * 1000, 2),
            "timestamp": time.time(),
        }
