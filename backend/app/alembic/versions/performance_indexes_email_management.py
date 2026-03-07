"""Add performance indexes for email management

Revision ID: perf_idx_email_mgmt
Revises: 4cbc48e9e690
Create Date: 2024-01-15 10:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "perf_idx_email_mgmt"
down_revision = "4cbc48e9e690"
branch_labels = None
depends_on = None


def upgrade():
    """Add performance indexes for email management"""

    # Index for account_id, is_read, and date (most common query pattern)
    op.create_index(
        "idx_email_account_user_status",
        "emails",
        ["account_id", "is_read", "date"],
        postgresql_ops={"date": "DESC"},
    )

    # Index for sender email and date
    op.create_index(
        "idx_email_sender_received", "emails", ["sender", "date"], postgresql_ops={"date": "DESC"}
    )

    # Full-text search index for subject (PostgreSQL GIN index)
    op.execute(
        """
        CREATE INDEX idx_email_subject_search
        ON emails USING gin(to_tsvector('english', subject))
    """
    )

    # Index for thread_id (for related emails)
    op.create_index("idx_email_thread_id", "emails", ["thread_id"])

    # Index for email_id in attachments table
    op.create_index("idx_attachment_email_id", "attachments", ["email_id"])

    # Index for is_flagged (for flagged email queries)
    op.create_index(
        "idx_email_flagged", "emails", ["is_flagged", "date"], postgresql_ops={"date": "DESC"}
    )

    # Index for category level
    op.create_index(
        "idx_email_category", "emails", ["category", "date"], postgresql_ops={"date": "DESC"}
    )

    # Composite index for common filtering combinations
    op.create_index(
        "idx_email_composite_filter",
        "emails",
        ["account_id", "is_read", "is_flagged", "date"],
        postgresql_ops={"date": "DESC"},
    )


def downgrade():
    """Remove performance indexes"""

    op.drop_index("idx_email_composite_filter", table_name="emails")
    op.drop_index("idx_email_category", table_name="emails")
    op.drop_index("idx_email_flagged", table_name="emails")
    op.drop_index("idx_attachment_email_id", table_name="attachments")
    op.drop_index("idx_email_thread_id", table_name="emails")
    op.execute("DROP INDEX IF EXISTS idx_email_subject_search")
    op.drop_index("idx_email_sender_received", table_name="emails")
    op.drop_index("idx_email_account_user_status", table_name="emails")
