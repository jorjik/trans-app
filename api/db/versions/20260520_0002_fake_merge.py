"""empty — migration 0002 was removed as redundant (ui_language already in initial)

Revision ID: 20260520_0002
Revises: 20260520_0001
Create Date: 2026-05-20 08:01:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260520_0002"
down_revision: Union[str, None] = "20260520_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Migration 20260520_0002 was removed as redundant — ui_language column
    was already included in the initial migration 20260520_0001. The database
    already has this revision stamped, so we keep this empty placeholder
    for alembic head tracking."""
    pass


def downgrade() -> None:
    pass
