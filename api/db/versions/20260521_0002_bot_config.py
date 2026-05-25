"""Add bot_config table for global bot settings (payment method visibility, etc.)

Revision ID: 20260521_0002
Revises: 20260521_0001
Create Date: 2026-05-21
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260521_0002"
down_revision: Union[str, None] = "20260521_0001"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.create_table(
        "bot_config",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("key", sa.String(64), nullable=False),
        sa.Column("value", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key"),
    )

    # Seed default payment methods config
    op.execute(
        sa.text(
            "INSERT INTO bot_config (key, value) "
            "VALUES ('payment_methods_visible', '{\"stars\": true, \"kofi\": true, \"paypal\": false}') 
            "ON CONFLICT (key) DO NOTHING"
        )
    )


def downgrade() -> None:
    op.drop_table("bot_config")
