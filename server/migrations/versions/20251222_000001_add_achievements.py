"""Add achievements table for kids gamification.

Revision ID: 004
Revises: 003
Create Date: 2024-12-22

This migration adds the achievements table for Wally Junior's
badge and reward system.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create achievements table
    op.create_table(
        "achievements",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("achievement_type", sa.String(50), nullable=False),
        sa.Column(
            "earned_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
        ),
        sa.Column("extra_data", postgresql.JSONB, server_default="{}"),
        sa.UniqueConstraint("user_id", "achievement_type", name="uq_user_achievement"),
    )
    op.create_index("idx_achievements_user", "achievements", ["user_id"])


def downgrade() -> None:
    op.drop_table("achievements")
