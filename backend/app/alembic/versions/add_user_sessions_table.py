"""Add user sessions table

Revision ID: user_sessions_table
Revises: perf_idx_email_mgmt
Create Date: 2024-01-15 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "user_sessions_table"
down_revision = "perf_idx_email_mgmt"
branch_labels = None
depends_on = None


def upgrade():
    """Add user_sessions table for tracking active accounts per user"""

    # Create user_sessions table
    op.create_table(
        "user_sessions",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("active_account_id", sa.String(length=36), nullable=True),
        sa.Column("auto_sync_enabled", sa.Boolean(), nullable=False, default=False),
        sa.Column("last_activity", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["active_account_id"],
            ["connected_accounts.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("user_id"),
    )

    # Create indexes for performance
    op.create_index("idx_user_sessions_active_account", "user_sessions", ["active_account_id"])
    op.create_index("idx_user_sessions_auto_sync", "user_sessions", ["auto_sync_enabled"])
    op.create_index("idx_user_sessions_last_activity", "user_sessions", ["last_activity"])


def downgrade():
    """Remove user_sessions table"""

    # Drop indexes
    op.drop_index("idx_user_sessions_last_activity", table_name="user_sessions")
    op.drop_index("idx_user_sessions_auto_sync", table_name="user_sessions")
    op.drop_index("idx_user_sessions_active_account", table_name="user_sessions")

    # Drop table
    op.drop_table("user_sessions")
