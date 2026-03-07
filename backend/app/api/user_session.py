"""
API endpoints for user session management and account switching
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.middleware.auth import get_current_user
from app.models.connected_account import ConnectedAccount
from app.models.user import User
from app.models.user_session import UserSession
from app.schemas.user_session import (
    EnableAutoSyncRequest,
    EnableAutoSyncResponse,
    SwitchAccountRequest,
    SwitchAccountResponse,
    UserSessionResponse,
    UserSessionStatusResponse,
)
from app.tasks.email_sync import sync_gmail_account

logger = logging.getLogger(__name__)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

# Create router
router = APIRouter(prefix="/user-session", tags=["user-session"])


def validate_account_id(account_id: str) -> bool:
    """
    Validate account ID format using UUID validation

    Args:
        account_id: The account ID to validate

    Returns:
        True if valid UUID format, False otherwise
    """
    if not account_id or not isinstance(account_id, str):
        return False

    try:
        uuid.UUID(account_id)
        return True
    except ValueError:
        return False


def validate_user_id(user_id: int) -> bool:
    """
    Validate user ID format

    Args:
        user_id: The user ID to validate

    Returns:
        True if valid positive integer, False otherwise
    """
    return isinstance(user_id, int) and user_id > 0


@router.get("/status", response_model=UserSessionStatusResponse)
@limiter.limit("60/minute")
async def get_user_session_status(
    request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> UserSessionStatusResponse:
    """
    Get current user session status and active account information
    """
    try:
        # Validate input parameters
        if not validate_user_id(current_user.id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID")

        # Get user session
        user_session = db.query(UserSession).filter(UserSession.user_id == current_user.id).first()

        # Get connected accounts count
        connected_accounts_count = (
            db.query(ConnectedAccount)
            .filter(
                ConnectedAccount.user_id == current_user.id, ConnectedAccount.is_active.is_(True)
            )
            .count()
        )

        if user_session:
            return UserSessionStatusResponse(
                has_active_account=user_session.active_account_id is not None,
                active_account_id=user_session.active_account_id,
                auto_sync_enabled=user_session.auto_sync_enabled,
                connected_accounts_count=connected_accounts_count,
                last_activity=user_session.last_activity,
            )
        else:
            return UserSessionStatusResponse(
                has_active_account=False,
                active_account_id=None,
                auto_sync_enabled=False,
                connected_accounts_count=connected_accounts_count,
                last_activity=datetime.now(timezone.utc),
            )

    except Exception as e:
        logger.error(f"Failed to get user session status for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve session status",
        )


@router.post("/switch-account", response_model=SwitchAccountResponse)
@limiter.limit("10/minute")
async def switch_active_account(
    request: Request,
    switch_request: SwitchAccountRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SwitchAccountResponse:
    """
    Switch the user's active account and trigger automatic sync
    """
    try:
        # Validate input parameters
        if not validate_account_id(switch_request.account_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid account ID format"
            )

        if not validate_user_id(current_user.id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID")

        # Start transaction with proper error handling
        try:
            # Validate account ownership with row-level locking
            account = (
                db.query(ConnectedAccount)
                .filter(
                    ConnectedAccount.id == switch_request.account_id,
                    ConnectedAccount.user_id == current_user.id,
                    ConnectedAccount.is_active.is_(True),
                )
                .with_for_update()
                .first()
            )

            if not account:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Account not found or access denied",
                )

            # Get or create user session with row-level locking
            user_session = (
                db.query(UserSession)
                .filter(UserSession.user_id == current_user.id)
                .with_for_update()
                .first()
            )

            previous_account_id = None
            sync_triggered = False

            if user_session:
                previous_account_id = user_session.active_account_id

                # Only update if switching to a different account
                if previous_account_id != switch_request.account_id:
                    user_session.active_account_id = switch_request.account_id
                    user_session.last_activity = datetime.now(timezone.utc)
                    user_session.updated_at = datetime.now(timezone.utc)

                    # Auto-sync is enabled per-account, not per-session
                    # The sync system will check if this account should be synced
                    logger.info(
                        f"User {current_user.id} switched from account {previous_account_id} to {switch_request.account_id}"
                    )
                else:
                    logger.info(
                        f"User {current_user.id} already has account {switch_request.account_id} as active"
                    )
            else:
                # Create new user session
                user_session = UserSession(
                    user_id=current_user.id,
                    active_account_id=switch_request.account_id,
                    auto_sync_enabled=False,  # Auto-sync is managed per-account, not per-session
                    last_activity=datetime.now(timezone.utc),
                )
                db.add(user_session)
                logger.info(
                    f"Created new user session for user {current_user.id} with active account {switch_request.account_id}"
                )

            # Commit transaction
            db.commit()

        except IntegrityError as e:
            db.rollback()
            logger.error(f"Database integrity error during account switch: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to switch account due to database error",
            )
        except Exception as e:
            db.rollback()
            logger.error(f"Database error during account switch: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to switch account"
            )
        db.refresh(user_session)

        # Trigger automatic sync for the new active account
        try:
            sync_gmail_account.delay(switch_request.account_id, current_user.id)
            sync_triggered = True
            logger.info(
                f"Triggered automatic sync for account {switch_request.account_id} after user {current_user.id} switched to it"
            )
        except Exception as sync_error:
            logger.error(
                f"Failed to trigger sync for account {switch_request.account_id}: {sync_error}"
            )
            # Don't fail the switch operation if sync fails

        return SwitchAccountResponse(
            success=True,
            message=f"Successfully switched to account {account.account_email}",
            previous_account_id=previous_account_id,
            new_account_id=switch_request.account_id,
            auto_sync_enabled=True,
            sync_triggered=sync_triggered,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to switch account for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to switch account"
        )


@router.post("/enable-auto-sync", response_model=EnableAutoSyncResponse)
@limiter.limit("10/minute")
async def enable_auto_sync(
    request: Request,
    enable_request: EnableAutoSyncRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EnableAutoSyncResponse:
    """
    Enable auto-sync for a specific account
    """
    try:
        # Validate input parameters
        if not validate_account_id(enable_request.account_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid account ID format"
            )

        if not validate_user_id(current_user.id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID")

        # Start transaction with proper error handling
        try:
            # Validate account ownership with row-level locking
            account = (
                db.query(ConnectedAccount)
                .filter(
                    ConnectedAccount.id == enable_request.account_id,
                    ConnectedAccount.user_id == current_user.id,
                    ConnectedAccount.is_active.is_(True),
                )
                .with_for_update()
                .first()
            )

            if not account:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Account not found or access denied",
                )

            # Get or create user session with row-level locking
            user_session = (
                db.query(UserSession)
                .filter(UserSession.user_id == current_user.id)
                .with_for_update()
                .first()
            )

            if user_session:
                # Check if the account is already the active account
                if user_session.active_account_id == enable_request.account_id:
                    # Account is already active, just enable auto-sync for this session
                    user_session.auto_sync_enabled = True
                    user_session.last_activity = datetime.now(timezone.utc)
                    user_session.updated_at = datetime.now(timezone.utc)
                    logger.info(
                        f"Auto-sync enabled for active account {enable_request.account_id} for user {current_user.id}"
                    )
                else:
                    # Switch to this account and enable auto-sync
                    user_session.active_account_id = enable_request.account_id
                    user_session.auto_sync_enabled = True
                    user_session.last_activity = datetime.now(timezone.utc)
                    user_session.updated_at = datetime.now(timezone.utc)
                    logger.info(
                        f"Switched to account {enable_request.account_id} and enabled auto-sync for user {current_user.id}"
                    )
            else:
                # Create new user session with this account as active
                user_session = UserSession(
                    user_id=current_user.id,
                    active_account_id=enable_request.account_id,
                    auto_sync_enabled=True,
                    last_activity=datetime.now(timezone.utc),
                )
                db.add(user_session)
                logger.info(
                    f"Created new user session with account {enable_request.account_id} and enabled auto-sync for user {current_user.id}"
                )

            # Commit transaction
            db.commit()

        except IntegrityError as e:
            db.rollback()
            logger.error(f"Database integrity error during auto-sync enable: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to enable auto-sync due to database error",
            )
        except Exception as e:
            db.rollback()
            logger.error(f"Database error during auto-sync enable: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to enable auto-sync",
            )

        return EnableAutoSyncResponse(
            success=True,
            message=f"Auto-sync enabled for account {account.account_email}",
            account_id=enable_request.account_id,
            auto_sync_enabled=True,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to enable auto-sync for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to enable auto-sync"
        )


@router.post("/disable-auto-sync", response_model=EnableAutoSyncResponse)
@limiter.limit("10/minute")
async def disable_auto_sync(
    request: Request,
    disable_request: EnableAutoSyncRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EnableAutoSyncResponse:
    """
    Disable auto-sync for the current session
    """
    try:
        # Validate input parameters
        if not validate_account_id(disable_request.account_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid account ID format"
            )

        if not validate_user_id(current_user.id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID")

        # Start transaction with proper error handling
        try:
            # Validate account ownership
            account = (
                db.query(ConnectedAccount)
                .filter(
                    ConnectedAccount.id == disable_request.account_id,
                    ConnectedAccount.user_id == current_user.id,
                    ConnectedAccount.is_active.is_(True),
                )
                .first()
            )

            if not account:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Account not found or access denied",
                )

            # Get user session with row-level locking
            user_session = (
                db.query(UserSession)
                .filter(UserSession.user_id == current_user.id)
                .with_for_update()
                .first()
            )

            if user_session:
                # Only disable if this is the active account
                if user_session.active_account_id == disable_request.account_id:
                    user_session.auto_sync_enabled = False
                    user_session.last_activity = datetime.now(timezone.utc)
                    user_session.updated_at = datetime.now(timezone.utc)
                    logger.info(
                        f"Auto-sync disabled for account {disable_request.account_id} for user {current_user.id}"
                    )
                else:
                    logger.info(
                        f"Account {disable_request.account_id} is not the active account for user {current_user.id}"
                    )
            else:
                logger.info(f"No user session found for user {current_user.id}")

            # Commit transaction
            db.commit()

        except IntegrityError as e:
            db.rollback()
            logger.error(f"Database integrity error during auto-sync disable: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to disable auto-sync due to database error",
            )
        except Exception as e:
            db.rollback()
            logger.error(f"Database error during auto-sync disable: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to disable auto-sync",
            )

        return EnableAutoSyncResponse(
            success=True,
            message=f"Auto-sync disabled for account {account.account_email}",
            account_id=disable_request.account_id,
            auto_sync_enabled=False,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to disable auto-sync for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to disable auto-sync"
        )


@router.get("/active-accounts", response_model=UserSessionResponse)
@limiter.limit("60/minute")
async def get_active_accounts_for_sync(
    request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> UserSessionResponse:
    """
    Get active accounts that should be synced (for internal use)
    """
    try:
        # Validate input parameters
        if not validate_user_id(current_user.id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID")

        # Get user session
        user_session = (
            db.query(UserSession)
            .filter(
                UserSession.user_id == current_user.id,
                UserSession.auto_sync_enabled.is_(True),
                UserSession.last_activity
                > datetime.now(timezone.utc) - timedelta(hours=1),  # Active within 1 hour
            )
            .first()
        )

        if user_session:
            return UserSessionResponse(
                user_id=user_session.user_id,
                active_account_id=user_session.active_account_id,
                auto_sync_enabled=user_session.auto_sync_enabled,
                last_activity=user_session.last_activity,
                created_at=user_session.created_at,
                updated_at=user_session.updated_at,
            )
        else:
            return UserSessionResponse(
                user_id=current_user.id,
                active_account_id=None,
                auto_sync_enabled=False,
                last_activity=datetime.now(timezone.utc),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

    except Exception as e:
        logger.error(f"Failed to get active accounts for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve active accounts",
        )
