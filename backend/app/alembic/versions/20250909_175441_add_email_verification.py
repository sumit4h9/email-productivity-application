"""add_email_verification

Revision ID: 20250909_175441
Revises: c3c5742fca1e
Create Date: 2025-09-09 17:54:41.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20250909_175441"
down_revision: Union[str, Sequence[str], None] = "c3c5742fca1e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add email_verified column to users table
    op.add_column(
        "users",
        sa.Column("email_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )

    # Create verification_codes table
    op.create_table(
        "verification_codes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("contact", sa.String(length=255), nullable=False),
        sa.Column("purpose", sa.String(length=20), nullable=False),
        sa.Column("code_hash", sa.String(length=128), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("used", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for verification_codes table
    op.create_index(
        "idx_verification_codes_user_id", "verification_codes", ["user_id"], unique=False
    )
    op.create_index(
        "idx_verification_codes_contact", "verification_codes", ["contact"], unique=False
    )
    op.create_index(
        "idx_verification_codes_purpose", "verification_codes", ["purpose"], unique=False
    )
    op.create_index(
        "idx_verification_codes_expires_at", "verification_codes", ["expires_at"], unique=False
    )
    op.create_index(
        "idx_verification_codes_used_expires",
        "verification_codes",
        ["used", "expires_at"],
        unique=False,
    )
    op.create_index(
        "idx_verification_codes_contact_purpose",
        "verification_codes",
        ["contact", "purpose"],
        unique=False,
    )
    op.create_index(op.f("ix_verification_codes_id"), "verification_codes", ["id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop verification_codes table and its indexes
    op.drop_index(op.f("ix_verification_codes_id"), table_name="verification_codes")
    op.drop_index("idx_verification_codes_contact_purpose", table_name="verification_codes")
    op.drop_index("idx_verification_codes_used_expires", table_name="verification_codes")
    op.drop_index("idx_verification_codes_expires_at", table_name="verification_codes")
    op.drop_index("idx_verification_codes_purpose", table_name="verification_codes")
    op.drop_index("idx_verification_codes_contact", table_name="verification_codes")
    op.drop_index("idx_verification_codes_user_id", table_name="verification_codes")
    op.drop_table("verification_codes")

    # Remove email_verified column from users table
    op.drop_column("users", "email_verified")
