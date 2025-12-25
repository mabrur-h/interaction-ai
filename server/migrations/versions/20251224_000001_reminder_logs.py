"""Add reminder_logs table and User.notification_settings.

Revision ID: 007
Revises: 006
Create Date: 2025-12-24

This migration adds:
- reminder_logs table for tracking sent payment reminders
- notification_settings JSONB column to users table
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add notification_settings to users table
    op.add_column(
        "users",
        sa.Column(
            "notification_settings",
            postgresql.JSONB,
            server_default='{"reminders_enabled": true, "reminder_time": "09:00", "channels": ["in_app"]}',
            nullable=False,
        ),
    )

    # Create reminder_logs table
    op.create_table(
        "reminder_logs",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "recurring_id",
            sa.BigInteger,
            sa.ForeignKey("recurring_transactions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("reminder_date", sa.Date, nullable=False),
        sa.Column("due_date", sa.Date, nullable=False),
        sa.Column(
            "sent_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("channel", sa.String(20), server_default="in_app", nullable=False),
        sa.UniqueConstraint(
            "user_id", "recurring_id", "reminder_date", name="uq_reminder_log"
        ),
    )
    op.create_index(
        "idx_reminder_logs_user_date",
        "reminder_logs",
        ["user_id", "reminder_date"],
    )


def downgrade() -> None:
    # Drop reminder_logs table
    op.drop_index("idx_reminder_logs_user_date", table_name="reminder_logs")
    op.drop_table("reminder_logs")

    # Remove notification_settings from users
    op.drop_column("users", "notification_settings")
