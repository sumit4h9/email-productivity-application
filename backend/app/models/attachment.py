from sqlalchemy import (  # type: ignore
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column  # type: ignore

from app.db.base import Base


class Attachment(Base):
    __tablename__ = "attachments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    email_id: Mapped[str] = mapped_column(String(36), ForeignKey("emails.id"), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type = Column(String(100), nullable=True)
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_key: Mapped[str] = mapped_column(String(255), nullable=False)
    checksum = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Database-level constraints and indexes
    __table_args__ = (
        Index("idx_attachments_email_id", "email_id"),
        Index("idx_attachments_storage_key", "storage_key"),
        Index("idx_attachments_content_type", "content_type"),
    )

    def __repr__(self):
        return f"<Attachment(id='{self.id}', email_id='{self.email_id}', filename='{self.filename}', size={self.size}, content_type='{self.content_type}')>"
