"""Add group_chat_configs table for group translation settings

Revision ID: 20260527_0001
Revises: 20260521_0002
Create Date: 2026-05-27
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260527_0001"
down_revision: Union[str, None] = "20260521_0002"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.create_table(
        "group_chat_configs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column("chat_title", sa.String(256), nullable=True),
        sa.Column("target_lang", sa.String(10), nullable=False, server_default=sa.text("'en'")),
        sa.Column("translator_uid", sa.BigInteger(), nullable=True,
                  comment="Telegram ID админа, включившего перевод"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("chat_id"),
    )
    op.create_index("ix_group_chat_configs_chat_id", "group_chat_configs", ["chat_id"])


def downgrade() -> None:
    op.drop_index("ix_group_chat_configs_chat_id")
    op.drop_table("group_chat_configs")
