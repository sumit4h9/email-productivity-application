from sqlalchemy import (  # type: ignore
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column  # type: ignore

from app.db.base import Base


class ConnectedAccount(Base):
    __tablename__ = "connected_accounts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    account_email: Mapped[str] = mapped_column(String(255), nullable=False)
    access_token_enc: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token_enc: Mapped[str] = mapped_column(Text, nullable=False)
    token_expiry = Column(DateTime(timezone=True), nullable=True)
    scope = Column(Text, nullable=True)
    sync_cursor = Column(String(255), nullable=True)
    last_synced_at = Column(DateTime(timezone=True), nullable=True)
    sync_status: Mapped[str] = mapped_column(String(20), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)

    # Database-level constraints and indexes
    __table_args__ = (
        UniqueConstraint("user_id", "provider", "account_email", name="uq_user_provider_email"),
        Index("idx_connected_accounts_user_id", "user_id"),
        Index("idx_connected_accounts_provider", "provider"),
        Index("idx_connected_accounts_sync_status", "sync_status"),
        Index("idx_connected_accounts_last_synced", "last_synced_at"),
    )

    def __repr__(self):
        return f"<ConnectedAccount(id='{self.id}', user_id={self.user_id}, provider='{self.provider}', account_email='{self.account_email}', is_active={self.is_active}, sync_status='{self.sync_status}')>"
