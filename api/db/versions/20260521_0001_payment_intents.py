"""Add payment_intents table for Ko-fi and PayPal.

Revision ID: 20260521_0001
Revises: 20260520_0002_fake_merge
Create Date: 2026-05-21
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260521_0001"
down_revision: Union[str, None] = "20260520_0002_fake_merge"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.create_table(
        "payment_intents",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("provider", sa.String(20), nullable=False),
        sa.Column("plan_id", sa.String(20), nullable=False),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("status", sa.String(20), server_default="pending", nullable=False),
        sa.Column("amount", sa.String(32), nullable=True),
        sa.Column("currency", sa.String(10), server_default="USD", nullable=False),
        sa.Column("external_id", sa.String(128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index(op.f("ix_payment_intents_code"), "payment_intents", ["code"])
    op.create_index(op.f("ix_payment_intents_user_id"), "payment_intents", ["user_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_payment_intents_code"), table_name="payment_intents")
    op.drop_index(op.f("ix_payment_intents_user_id"), table_name="payment_intents")
    op.drop_table("payment_intents")
