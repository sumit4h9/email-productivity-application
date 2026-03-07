from sqlalchemy import (  # type: ignore
    Boolean,
    Column,
    DateTime,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column  # type: ignore

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    username: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Database-level constraints
    __table_args__ = (
        UniqueConstraint(
            "email", name="uq_users_email"
        ),  # Case-insensitive uniqueness handled in application
        UniqueConstraint("username", name="uq_users_username"),  # Username uniqueness
        Index("idx_users_email_active", "email", "is_active"),  # Composite index for common queries
        Index(
            "idx_users_username_active", "username", "is_active"
        ),  # Composite index for username queries
        Index("idx_users_created_at", "created_at"),  # Index for time-based queries
    )

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', username='{self.username}', is_active={self.is_active}, email_verified={self.email_verified})>"
