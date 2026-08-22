"""merge heads

Revision ID: 8f7cca35f24e
Revises: 789fd266a955, user_sessions_table
Create Date: 2026-08-23 03:00:45.384414

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8f7cca35f24e'
down_revision: Union[str, Sequence[str], None] = ('789fd266a955', 'user_sessions_table')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
