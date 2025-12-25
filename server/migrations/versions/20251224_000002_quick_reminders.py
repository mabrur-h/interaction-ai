"""Add quick_reminders table for short-term Celery ETA reminders.

Revision ID: 008
Revises: 007
Create Date: 2025-12-24

This migration adds:
- quick_reminders table for short-term reminders (30 min - 24 hours)
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create quick_reminders table
    op.create_table(
        "quick_reminders",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("message", sa.String(500), nullable=False),
        sa.Column("amount", sa.BigInteger, nullable=True),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("remind_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("celery_task_id", sa.String(255), nullable=True),
        sa.Column("status", sa.String(20), server_default="pending", nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "idx_quick_reminders_user_status",
        "quick_reminders",
        ["user_id", "status"],
    )
    op.create_index(
        "idx_quick_reminders_remind_at",
        "quick_reminders",
        ["remind_at"],
    )


def downgrade() -> None:
    # Drop quick_reminders table
    op.drop_index("idx_quick_reminders_remind_at", table_name="quick_reminders")
    op.drop_index("idx_quick_reminders_user_status", table_name="quick_reminders")
    op.drop_table("quick_reminders")
