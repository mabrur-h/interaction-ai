"""Remove Wally Junior (kids) tables and columns.

Revision ID: 006
Revises: 005
Create Date: 2025-12-23

This migration removes all kids-related tables and user columns
as the kids app is being moved to a separate backend.

Tables removed:
- achievements
- expenses
- savings_goals
- family_relationships
- invite_codes

User columns removed:
- user_type
- password_hash
- initial_balance
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop kids tables
    op.drop_table("achievements")
    op.drop_table("invite_codes")
    op.drop_table("savings_goals")
    op.drop_table("expenses")
    op.drop_table("family_relationships")

    # Drop kids columns from users table
    op.drop_column("users", "initial_balance")
    op.drop_column("users", "password_hash")
    op.drop_column("users", "user_type")


def downgrade() -> None:
    # Restore user columns
    op.add_column(
        "users",
        sa.Column("user_type", sa.String(20), server_default="adult", nullable=False),
    )
    op.add_column(
        "users",
        sa.Column("password_hash", sa.String(255), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("initial_balance", sa.BigInteger, server_default="0", nullable=False),
    )

    # Restore family_relationships table
    op.create_table(
        "family_relationships",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column(
            "parent_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "child_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("relationship_type", sa.String(50), server_default="parent"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
        ),
        sa.UniqueConstraint("parent_id", "child_id", name="uq_family_parent_child"),
    )
    op.create_index("idx_family_parent", "family_relationships", ["parent_id"])
    op.create_index("idx_family_child", "family_relationships", ["child_id"])

    # Restore expenses table
    op.create_table(
        "expenses",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("amount", sa.BigInteger, nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column(
            "expense_date",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index("idx_expenses_user_date", "expenses", ["user_id", "expense_date"])

    # Restore savings_goals table
    op.create_table(
        "savings_goals",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("target_amount", sa.BigInteger, nullable=False),
        sa.Column("current_amount", sa.BigInteger, server_default="0"),
        sa.Column("status", sa.String(50), server_default="active"),
        sa.Column("emoji", sa.String(10), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_savings_user_status", "savings_goals", ["user_id", "status"])

    # Restore invite_codes table
    op.create_table(
        "invite_codes",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(20), unique=True, nullable=False),
        sa.Column(
            "parent_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("child_name", sa.String(255), nullable=False),
        sa.Column("initial_balance", sa.BigInteger, server_default="0"),
        sa.Column("used", sa.Boolean, server_default="false"),
        sa.Column("used_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index("idx_invite_code", "invite_codes", ["code"])

    # Restore achievements table
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
