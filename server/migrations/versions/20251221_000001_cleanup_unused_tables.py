"""Remove unused triggers and gmail_seen_messages tables.

Revision ID: 003
Revises: 002
Create Date: 2024-12-21

This migration removes tables that are no longer used after the
Gmail/Calendar/Triggers cleanup for Wally Junior.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop unused tables
    op.drop_table("gmail_seen_messages")
    op.drop_table("triggers")

    # Clean up OAuth connections for removed providers
    op.execute(
        "DELETE FROM oauth_connections WHERE provider IN ('gmail', 'calendar')"
    )


def downgrade() -> None:
    # Recreate triggers table
    op.create_table(
        "triggers",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("tool_name", sa.String(100), nullable=False),
        sa.Column("tool_args", postgresql.JSONB, server_default="{}"),
        sa.Column("frequency", sa.String(50), nullable=False),
        sa.Column("next_trigger", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_triggered", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index(
        "idx_triggers_due",
        "triggers",
        ["status", "next_trigger"],
        postgresql_where=sa.text("status = 'active'"),
    )

    # Recreate gmail_seen_messages table
    op.create_table(
        "gmail_seen_messages",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("message_id", sa.String(255), nullable=False),
        sa.Column("thread_id", sa.String(255), nullable=True),
        sa.Column(
            "processed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
        ),
        sa.UniqueConstraint("user_id", "message_id", name="uq_gmail_user_message"),
    )
    op.create_index(
        "idx_gmail_seen_user",
        "gmail_seen_messages",
        ["user_id", "processed_at"],
    )
