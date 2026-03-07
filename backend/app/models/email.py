from sqlalchemy import (  # type: ignore
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column  # type: ignore

from app.db.base import Base


class Email(Base):
    __tablename__ = "emails"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    account_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("connected_accounts.id"), nullable=False
    )
    provider_message_id: Mapped[str] = mapped_column(String(255), nullable=False)
    thread_id = Column(String(255), nullable=True)
    subject = Column(Text, nullable=True)
    sender = Column(String(255), nullable=True)
    recipients = Column(Text, nullable=True)
    snippet = Column(Text, nullable=True)
    date = Column(DateTime(timezone=True), nullable=True)
    body_text = Column(Text, nullable=True)
    body_storage_key = Column(String(255), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_flagged: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    ml_processed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_phishing = Column(Boolean, nullable=True)
    phishing_score = Column(Float, nullable=True)
    category = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)

    # Database-level constraints and indexes
    __table_args__ = (
        Index("idx_emails_account_id", "account_id"),
        Index("idx_emails_account_date", "account_id", "date"),
        Index("idx_emails_date", "date"),
        Index("idx_emails_sender", "sender"),
        Index("idx_emails_thread_id", "thread_id"),
        Index("idx_emails_provider_message_id", "provider_message_id"),
        Index("idx_emails_is_read", "is_read"),
        Index("idx_emails_is_flagged", "is_flagged"),
        Index("idx_emails_ml_processed", "ml_processed"),
    )

    def __repr__(self):
        return f"<Email(id='{self.id}', account_id='{self.account_id}', provider_message_id='{self.provider_message_id}', subject='{self.subject[:50] if self.subject else None}...', is_read={self.is_read}, is_flagged={self.is_flagged})>"
