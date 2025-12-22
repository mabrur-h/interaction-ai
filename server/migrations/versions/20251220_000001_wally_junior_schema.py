"""Wally Junior schema additions.

Revision ID: 002
Revises: 001
Create Date: 2024-12-20

This migration adds tables for Wally Junior kids finance app:
- User table additions: user_type, password_hash, initial_balance
- family_relationships: Parent-child connections
- expenses: Manual expense entries
- savings_goals: Piggy bank targets
- invite_codes: For child account creation
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns to users table
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

    # Make google_id nullable for child accounts (they use password auth)
    op.alter_column(
        "users",
        "google_id",
        existing_type=sa.String(255),
        nullable=True,
    )

    # Family relationships table
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

    # Expenses table
    op.create_table(
        "expenses",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("amount", sa.BigInteger, nullable=False),  # In cents
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

    # Savings goals table
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
        sa.Column("target_amount", sa.BigInteger, nullable=False),  # In cents
        sa.Column("current_amount", sa.BigInteger, server_default="0"),  # In cents
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

    # Invite codes table
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
        sa.Column("initial_balance", sa.BigInteger, server_default="0"),  # In cents
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


def downgrade() -> None:
    op.drop_table("invite_codes")
    op.drop_table("savings_goals")
    op.drop_table("expenses")
    op.drop_table("family_relationships")

    op.drop_column("users", "initial_balance")
    op.drop_column("users", "password_hash")
    op.drop_column("users", "user_type")

    # Restore google_id to non-nullable (this may fail if there are null values)
    op.alter_column(
        "users",
        "google_id",
        existing_type=sa.String(255),
        nullable=False,
    )
