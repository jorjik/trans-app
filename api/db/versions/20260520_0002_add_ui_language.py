"""add users.ui_language column

Revision ID: 20260520_0002
Revises: 20260520_0001
Create Date: 2026-05-20 10:00:00
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
    op.add_column(
        "users",
        sa.Column("ui_language", sa.String(length=10), nullable=False, server_default=sa.text("'en'")),
    )


def downgrade() -> None:
    op.drop_column("users", "ui_language")
