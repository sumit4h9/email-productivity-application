from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class VerificationCode(Base):
    __tablename__ = "verification_codes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    contact: Mapped[str] = mapped_column(String(255), nullable=False)  # email address
    purpose: Mapped[str] = mapped_column(String(20), nullable=False)  # "signup" or "login"
    code_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    expires_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Database-level constraints and indexes
    __table_args__ = (
        Index("idx_verification_codes_user_id", "user_id"),
        Index("idx_verification_codes_contact", "contact"),
        Index("idx_verification_codes_purpose", "purpose"),
        Index("idx_verification_codes_expires_at", "expires_at"),
        Index("idx_verification_codes_used_expires", "used", "expires_at"),
        Index("idx_verification_codes_contact_purpose", "contact", "purpose"),
    )

    def __repr__(self):
        return f"<VerificationCode(id={self.id}, user_id={self.user_id}, contact='{self.contact}', purpose='{self.purpose}', used={self.used}, expires_at='{self.expires_at}')>"
