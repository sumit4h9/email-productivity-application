"""add_username_remove_name_from_users

Revision ID: d4f8e9a2b3c1
Revises: a07f79215ec2
Create Date: 2024-01-15 10:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d4f8e9a2b3c1"
down_revision = "a07f79215ec2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add username column as nullable first
    op.add_column("users", sa.Column("username", sa.String(length=50), nullable=True))

    # Update existing users to have usernames based on their email
    # This generates usernames from email addresses for existing users
    op.execute(
        """
        UPDATE users
        SET username = LOWER(SPLIT_PART(email, '@', 1)) || '_' || id::text
        WHERE username IS NULL
    """
    )

    # Now make username non-nullable
    op.alter_column("users", "username", nullable=False)

    # Create unique constraint for username
    op.create_unique_constraint("uq_users_username", "users", ["username"])

    # Create index for username queries
    op.create_index("idx_users_username_active", "users", ["username", "is_active"])

    # Remove name column
    op.drop_column("users", "name")


def downgrade() -> None:
    # Add name column back
    op.add_column("users", sa.Column("name", sa.String(length=100), nullable=True))

    # Drop username index
    op.drop_index("idx_users_username_active", table_name="users")

    # Drop username unique constraint
    op.drop_constraint("uq_users_username", "users", type_="unique")

    # Drop username column
    op.drop_column("users", "username")
