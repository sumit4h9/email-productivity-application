"""
UserSession model for tracking active accounts per user
"""

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserSession(Base):
    """
    Tracks which account a user is currently actively using
    Only the active account gets automatic background sync
    """

    __tablename__ = "user_sessions"

    # Primary key - one session per user
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), primary_key=True)

    # Currently active account for this user
    active_account_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("connected_accounts.id"), nullable=True
    )

    # Whether auto-sync is enabled for the active account
    # Only enabled after user has interacted with the account
    auto_sync_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Track user activity for sync decisions
    last_activity: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self):
        return f"<UserSession(user_id={self.user_id}, active_account_id={self.active_account_id}, auto_sync_enabled={self.auto_sync_enabled})>"
