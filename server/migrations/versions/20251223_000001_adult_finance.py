"""Add adult finance tables (Transaction, Budget, Debt, RecurringTransaction, ExchangeRate).

Revision ID: 005
Revises: 004
Create Date: 2025-12-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add currency fields to users table
    op.add_column(
        "users",
        sa.Column("primary_currency", sa.String(3), server_default="UZS", nullable=False),
    )
    op.add_column(
        "users",
        sa.Column("currency_settings", postgresql.JSONB, server_default="{}", nullable=False),
    )

    # Create recurring_transactions table first (referenced by transactions)
    op.create_table(
        "recurring_transactions",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("template", postgresql.JSONB, nullable=False),
        sa.Column("frequency", sa.String(20), nullable=False),
        sa.Column("next_due_date", sa.Date, nullable=False),
        sa.Column("last_processed_date", sa.Date, nullable=True),
        sa.Column("reminder_days_before", sa.BigInteger, nullable=True),
        sa.Column("is_active", sa.Boolean, server_default="true", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "idx_recurring_user_active",
        "recurring_transactions",
        ["user_id", "is_active"],
    )
    op.create_index(
        "idx_recurring_next_due",
        "recurring_transactions",
        ["next_due_date", "is_active"],
    )

    # Create transactions table
    op.create_table(
        "transactions",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("amount", sa.BigInteger, nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("amount_primary", sa.BigInteger, nullable=False),
        sa.Column("exchange_rate", sa.Numeric(18, 8), nullable=True),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("counterparty", sa.String(255), nullable=True),
        sa.Column(
            "transaction_date",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("is_recurring", sa.Boolean, server_default="false", nullable=False),
        sa.Column(
            "recurring_id",
            sa.BigInteger,
            sa.ForeignKey("recurring_transactions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("tags", postgresql.JSONB, server_default="[]", nullable=False),
        sa.Column("extra_data", postgresql.JSONB, server_default="{}", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "idx_transactions_user_date",
        "transactions",
        ["user_id", "transaction_date"],
    )
    op.create_index(
        "idx_transactions_user_type",
        "transactions",
        ["user_id", "type"],
    )
    op.create_index(
        "idx_transactions_user_category",
        "transactions",
        ["user_id", "category"],
    )

    # Create budgets table
    op.create_table(
        "budgets",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("monthly_limit", sa.BigInteger, nullable=False),
        sa.Column("alert_threshold", sa.BigInteger, server_default="80", nullable=False),
        sa.Column("is_active", sa.Boolean, server_default="true", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id", "category", name="uq_budget_user_category"),
    )
    op.create_index(
        "idx_budgets_user_active",
        "budgets",
        ["user_id", "is_active"],
    )

    # Create debts table
    op.create_table(
        "debts",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("counterparty_name", sa.String(255), nullable=False),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("original_amount", sa.BigInteger, nullable=False),
        sa.Column("remaining_amount", sa.BigInteger, nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("due_date", sa.Date, nullable=True),
        sa.Column("status", sa.String(20), server_default="active", nullable=False),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "idx_debts_user_status",
        "debts",
        ["user_id", "status"],
    )

    # Create exchange_rates table
    op.create_table(
        "exchange_rates",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("from_currency", sa.String(3), nullable=False),
        sa.Column("to_currency", sa.String(3), nullable=False),
        sa.Column("rate", sa.Numeric(18, 8), nullable=False),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "from_currency", "to_currency", "date", name="uq_exchange_rate"
        ),
    )
    op.create_index(
        "idx_exchange_rate_lookup",
        "exchange_rates",
        ["from_currency", "to_currency", "date"],
    )


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index("idx_exchange_rate_lookup", table_name="exchange_rates")
    op.drop_table("exchange_rates")

    op.drop_index("idx_debts_user_status", table_name="debts")
    op.drop_table("debts")

    op.drop_index("idx_budgets_user_active", table_name="budgets")
    op.drop_table("budgets")

    op.drop_index("idx_transactions_user_category", table_name="transactions")
    op.drop_index("idx_transactions_user_type", table_name="transactions")
    op.drop_index("idx_transactions_user_date", table_name="transactions")
    op.drop_table("transactions")

    op.drop_index("idx_recurring_next_due", table_name="recurring_transactions")
    op.drop_index("idx_recurring_user_active", table_name="recurring_transactions")
    op.drop_table("recurring_transactions")

    # Remove columns from users
    op.drop_column("users", "currency_settings")
    op.drop_column("users", "primary_currency")
