"""
OAuth API endpoints for Google account integration and email synchronization
"""

import logging
from datetime import datetime, timezone
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.core import (
    exchange_code_for_tokens,
    get_google_oauth_url,
    validate_oauth_config,
)
from app.db.session import get_db
from app.middleware.auth import get_current_user
from app.models.connected_account import ConnectedAccount
from app.models.user import User
from app.models.user_session import UserSession
from app.schemas.oauth import (
    AccountListResponse,
    AccountStatusResponse,
    DisconnectResponse,
    OAuthCallbackRequest,
    OAuthCallbackResponse,
    OAuthUrlResponse,
    SyncTriggerResponse,
)
from app.tasks.email_sync import manual_refresh_account, sync_gmail_account
from app.utils.encryption import encrypt_credentials

logger = logging.getLogger(__name__)
security = HTTPBearer()

# Rate limiter setup
limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/oauth", tags=["OAuth"])


@router.get("/google/url", response_model=OAuthUrlResponse)
@limiter.limit("10/minute")
async def get_google_oauth_url_endpoint(
    request: Request, current_user: User = Depends(get_current_user)
) -> OAuthUrlResponse:
    """
    Get Google OAuth authorization URL for the current user

    Returns:
        Dict containing the authorization URL
    """
    try:
        if not validate_oauth_config():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="OAuth service is not properly configured",
            )

        authorization_url = get_google_oauth_url()

        logger.info(f"Generated OAuth URL for user {current_user.id}")
        return OAuthUrlResponse(authorization_url=authorization_url)

    except Exception as e:
        logger.error(f"Failed to generate OAuth URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate authorization URL",
        )


@router.post("/google/callback", response_model=OAuthCallbackResponse)
@limiter.limit("5/minute")
async def google_oauth_callback(
    request: Request,
    callback_request: OAuthCallbackRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OAuthCallbackResponse:
    """
    Handle Google OAuth callback and store account credentials

    Args:
        request: FastAPI request object for rate limiting
        callback_request: OAuth callback request containing authorization code

    Returns:
        OAuthCallbackResponse containing account information and sync status
    """
    try:
        # Validate authorization code format (consistent with core/oauth.py)
        if not callback_request.code or len(callback_request.code) < 43 or len(callback_request.code) > 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid authorization code length"
            )

        # Validate Google authorization code format
        import re
        if not re.match(r"^4/[0-9A-Za-z\-_\.]+$", callback_request.code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid authorization code format"
            )

        # Exchange code for tokens
        credentials, user_info = exchange_code_for_tokens(callback_request.code)

        # Check if account already exists
        existing_account = (
            db.query(ConnectedAccount)
            .filter(
                ConnectedAccount.user_id == current_user.id,
                ConnectedAccount.provider == "google",
                ConnectedAccount.account_email == user_info["email"],
            )
            .first()
        )

        # Encrypt credentials properly
        encrypted_access, encrypted_refresh = encrypt_credentials(
            credentials.token, credentials.refresh_token
        )

        if existing_account:
            # Update existing account
            existing_account.access_token_enc = encrypted_access
            existing_account.refresh_token_enc = encrypted_refresh
            existing_account.token_expiry = credentials.expiry
            existing_account.is_active = True
            db.commit()

            account = existing_account
            logger.info(
                f"Updated existing Google account for user {current_user.id}: {user_info['email']}"
            )
        else:
            # Create new account
            account = ConnectedAccount(
                id=uuid.uuid4().hex,
                user_id=current_user.id,
                provider="google",
                account_email=user_info["email"],
                access_token_enc=encrypted_access,
                refresh_token_enc=encrypted_refresh,
                token_expiry=credentials.expiry,
                scope=",".join(credentials.scopes) if credentials.scopes else None,
                sync_status="pending",
                is_active=True,
                created_at=datetime.now(timezone.utc),   # <-- must set
                updated_at=datetime.now(timezone.utc),
            )
            db.add(account)
            db.commit()
            db.refresh(account)

            logger.info(
                f"Created new Google account for user {current_user.id}: {user_info['email']}"
            )

        # Set this account as the user's active account if they don't have one
        user_session = db.query(UserSession).filter(UserSession.user_id == current_user.id).first()

        if not user_session:
            # Create new user session with this account as active
            user_session = UserSession(
                user_id=current_user.id,
                active_account_id=account.id,
                auto_sync_enabled=True,  # Enable auto-sync for first connected account
                last_activity=datetime.now(timezone.utc),
            )
            db.add(user_session)
            db.commit()
            logger.info(
                f"Created user session for user {current_user.id} with active account {account.id}"
            )
        elif not user_session.active_account_id:
            # User has a session but no active account, set this one as active
            user_session.active_account_id = account.id
            user_session.auto_sync_enabled = True
            user_session.last_activity = datetime.now(timezone.utc)
            user_session.updated_at = datetime.now(timezone.utc)
            db.commit()
            logger.info(f"Set account {account.id} as active for user {current_user.id}")

        # Trigger initial sync
        sync_task = sync_gmail_account.delay(account.id, current_user.id)

        return OAuthCallbackResponse(
            account_id=account.id,
            provider=account.provider,
            account_email=account.account_email,
            status="connected",
            sync_task_id=sync_task.id,
            message="Account connected successfully. Email sync started.",
        )

    except Exception as e:
        logger.error(f"OAuth callback failed for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to connect Google account"
        )


@router.get("/accounts", response_model=AccountListResponse)
async def list_connected_accounts(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> AccountListResponse:
    """
    List all connected accounts for the current user

    Returns:
        Dict containing list of connected accounts
    """
    try:
        accounts = (
            db.query(ConnectedAccount)
            .filter(
                ConnectedAccount.user_id == current_user.id, ConnectedAccount.is_active.is_(True)
            )
            .all()
        )

        account_list = []
        for account in accounts:
            account_list.append(
                {
                    "id": account.id,
                    "provider": account.provider,
                    "account_email": account.account_email,
                    "last_synced_at": account.last_synced_at,
                    "sync_status": account.sync_status,
                    "is_active": account.is_active,
                    "created_at": account.created_at,
                }
            )

        logger.info(f"Listed {len(account_list)} accounts for user {current_user.id}")
        return {"accounts": account_list}

    except Exception as e:
        logger.error(f"Failed to list accounts for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve connected accounts",
        )


@router.post("/accounts/{account_id}/sync", response_model=SyncTriggerResponse)
@limiter.limit("20/minute")
async def trigger_manual_sync(
    request: Request,
    account_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SyncTriggerResponse:
    """
    Trigger manual email sync for a specific account

    Args:
        account_id: ID of the account to sync

    Returns:
        SyncTriggerResponse containing sync task information
    """
    try:
        # Validate account ID format (accept both UUID with hyphens and hex format)
        if not account_id or len(account_id) < 32 or len(account_id) > 36:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid account ID format"
            )

        # Normalize account ID to hex format for database lookup
        normalized_account_id = account_id
        if len(account_id) == 36 and "-" in account_id:
            # Convert UUID with hyphens to hex format
            try:
                normalized_account_id = str(uuid.UUID(account_id)).replace("-", "")
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid account ID format"
                )

        # Verify account ownership
        account = (
            db.query(ConnectedAccount)
            .filter(
                ConnectedAccount.id == normalized_account_id,
                ConnectedAccount.user_id == current_user.id,
                ConnectedAccount.is_active.is_(True),
            )
            .first()
        )

        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Account not found or access denied"
            )

        # Trigger manual refresh
        sync_task = manual_refresh_account.delay(account_id, current_user.id)

        logger.info(f"Triggered manual sync for account {account_id}, user {current_user.id}")
        return SyncTriggerResponse(
            account_id=account_id,
            task_id=sync_task.id,
            status="sync_started",
            message="Manual sync triggered successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger sync for account {account_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to trigger email sync"
        )


@router.delete("/accounts/{account_id}", response_model=DisconnectResponse)
@limiter.limit("10/minute")
async def disconnect_account(
    request: Request,
    account_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DisconnectResponse:
    """
    Disconnect and deactivate a connected account

    Args:
        request: FastAPI request object for rate limiting
        account_id: ID of the account to disconnect

    Returns:
        DisconnectResponse containing success message
    """
    try:
        # Validate account ID format (accept both UUID with hyphens and hex format)
        if not account_id or len(account_id) < 32 or len(account_id) > 36:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid account ID format"
            )

        # Normalize account ID to hex format for database lookup
        if len(account_id) == 36 and "-" in account_id:
            # Convert UUID with hyphens to hex format
            try:
                account_id = str(uuid.UUID(account_id)).replace("-", "")
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid account ID format"
                )

        # Verify account ownership
        account = (
            db.query(ConnectedAccount)
            .filter(ConnectedAccount.id == account_id, ConnectedAccount.user_id == current_user.id)
            .first()
        )

        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Account not found or access denied"
            )

        # Deactivate account
        account.is_active = False
        account.sync_status = "disconnected"
        db.commit()

        logger.info(f"Disconnected account {account_id} for user {current_user.id}")
        return DisconnectResponse(message="Account disconnected successfully")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to disconnect account {account_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to disconnect account"
        )


@router.get("/accounts/{account_id}/status", response_model=AccountStatusResponse)
@limiter.limit("30/minute")
async def get_account_status(
    request: Request,
    account_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AccountStatusResponse:
    """
    Get detailed status information for a specific account

    Args:
        request: FastAPI request object for rate limiting
        account_id: ID of the account to check

    Returns:
        AccountStatusResponse containing account status information
    """
    try:
        # Validate account ID format (accept both UUID with hyphens and hex format)
        if not account_id or len(account_id) < 32 or len(account_id) > 36:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid account ID format"
            )

        # Normalize account ID to hex format for database lookup
        normalized_account_id = account_id
        if len(account_id) == 36 and "-" in account_id:
            # Convert UUID with hyphens to hex format
            try:
                normalized_account_id = str(uuid.UUID(account_id)).replace("-", "")
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid account ID format"
                )

        # Verify account ownership
        account = (
            db.query(ConnectedAccount)
            .filter(ConnectedAccount.id == normalized_account_id, ConnectedAccount.user_id == current_user.id)
            .first()
        )

        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Account not found or access denied"
            )

        return AccountStatusResponse(
            id=account.id,
            provider=account.provider,
            account_email=account.account_email,
            sync_status=account.sync_status,
            last_synced_at=account.last_synced_at,
            is_active=account.is_active,
            created_at=account.created_at,
            updated_at=account.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get account status for {account_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve account status",
        )
