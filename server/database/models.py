"""SQLAlchemy ORM models for OpenPoke."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    BigInteger,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


class User(Base):
    """User model - central identity management."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    google_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    timezone: Mapped[str] = mapped_column(String(100), default="UTC")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Wally Junior fields
    user_type: Mapped[str] = mapped_column(String(20), default="adult")  # 'adult' | 'child'
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # For child login
    initial_balance: Mapped[int] = mapped_column(BigInteger, default=0)  # Starting allowance in cents

    # Adult finance fields
    primary_currency: Mapped[str] = mapped_column(String(3), default="UZS")  # ISO 4217 code
    currency_settings: Mapped[dict] = mapped_column(
        JSONB, default=dict
    )  # {display_currencies: [], auto_convert: bool}

    # Relationships
    sessions: Mapped[list["Session"]] = relationship(
        "Session", back_populates="user", cascade="all, delete-orphan"
    )
    oauth_connections: Mapped[list["OAuthConnection"]] = relationship(
        "OAuthConnection", back_populates="user", cascade="all, delete-orphan"
    )
    conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation", back_populates="user", cascade="all, delete-orphan"
    )
    execution_logs: Mapped[list["ExecutionLog"]] = relationship(
        "ExecutionLog", back_populates="user", cascade="all, delete-orphan"
    )
    agent_roster: Mapped[list["AgentRoster"]] = relationship(
        "AgentRoster", back_populates="user", cascade="all, delete-orphan"
    )
    working_memory: Mapped[Optional["WorkingMemory"]] = relationship(
        "WorkingMemory", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


class Session(Base):
    """Session model - JWT refresh token tracking."""

    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    refresh_token_hash: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(INET, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="sessions")

    __table_args__ = (Index("idx_sessions_user_id", "user_id"),)


class OAuthConnection(Base):
    """OAuth connection model - Composio integrations per user."""

    __tablename__ = "oauth_connections"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    provider: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # 'gmail', 'calendar'
    composio_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    composio_connection_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    provider_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    extra_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="oauth_connections")

    __table_args__ = (
        UniqueConstraint("user_id", "provider", name="uq_oauth_user_provider"),
    )


class Conversation(Base):
    """Conversation model - chat sessions."""

    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="conversations")
    messages: Mapped[list["Message"]] = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("idx_conversations_user", "user_id"),)


class Message(Base):
    """Message model - individual chat messages."""

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # 'user', 'assistant', 'agent'
    content: Mapped[str] = mapped_column(Text, nullable=False)
    extra_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    conversation: Mapped["Conversation"] = relationship(
        "Conversation", back_populates="messages"
    )

    __table_args__ = (Index("idx_messages_conv_time", "conversation_id", "created_at"),)


class ExecutionLog(Base):
    """Execution log model - agent execution history."""

    __tablename__ = "execution_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    agent_name: Mapped[str] = mapped_column(String(255), nullable=False)
    tag: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # 'agent_request', 'agent_action', 'tool_response', 'agent_response'
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="execution_logs")

    __table_args__ = (
        Index("idx_exec_logs_user_agent", "user_id", "agent_name", "created_at"),
    )


class AgentRoster(Base):
    """Agent roster model - registered agents per user."""

    __tablename__ = "agent_roster"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    agent_name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="agent_roster")

    __table_args__ = (
        UniqueConstraint("user_id", "agent_name", name="uq_agent_roster_user_agent"),
    )


class WorkingMemory(Base):
    """Working memory model - conversation summary per user."""

    __tablename__ = "working_memory"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="working_memory")

    __table_args__ = (Index("idx_working_memory_user", "user_id", unique=True),)


# =============================================================================
# Wally Junior Models
# =============================================================================


class FamilyRelationship(Base):
    """Family relationship model - links parents to children."""

    __tablename__ = "family_relationships"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    parent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    child_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    relationship_type: Mapped[str] = mapped_column(
        String(50), default="parent"
    )  # 'parent', 'guardian'
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    parent: Mapped["User"] = relationship("User", foreign_keys=[parent_id])
    child: Mapped["User"] = relationship("User", foreign_keys=[child_id])

    __table_args__ = (
        UniqueConstraint("parent_id", "child_id", name="uq_family_parent_child"),
        Index("idx_family_parent", "parent_id"),
        Index("idx_family_child", "child_id"),
    )


class Expense(Base):
    """Expense model - manual expense entries for kids."""

    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)  # In cents
    category: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # food, toys, games, clothes, books, entertainment, other
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expense_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User")

    __table_args__ = (Index("idx_expenses_user_date", "user_id", "expense_date"),)


class SavingsGoal(Base):
    """Savings goal model - piggy bank targets for kids."""

    __tablename__ = "savings_goals"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    target_amount: Mapped[int] = mapped_column(BigInteger, nullable=False)  # In cents
    current_amount: Mapped[int] = mapped_column(BigInteger, default=0)  # In cents
    status: Mapped[str] = mapped_column(
        String(50), default="active"
    )  # 'active', 'completed', 'abandoned'
    emoji: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User")

    __table_args__ = (Index("idx_savings_user_status", "user_id", "status"),)


class InviteCode(Base):
    """Invite code model - for parent-created child accounts."""

    __tablename__ = "invite_codes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    parent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    child_name: Mapped[str] = mapped_column(String(255), nullable=False)
    initial_balance: Mapped[int] = mapped_column(BigInteger, default=0)  # In cents
    used: Mapped[bool] = mapped_column(Boolean, default=False)
    used_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    parent: Mapped["User"] = relationship("User", foreign_keys=[parent_id])

    __table_args__ = (Index("idx_invite_code", "code"),)


class Achievement(Base):
    """Achievement model - badges and rewards for kids."""

    __tablename__ = "achievements"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    achievement_type: Mapped[str] = mapped_column(String(50), nullable=False)
    earned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    extra_data: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Relationships
    user: Mapped["User"] = relationship("User")

    __table_args__ = (
        UniqueConstraint("user_id", "achievement_type", name="uq_user_achievement"),
        Index("idx_achievements_user", "user_id"),
    )


# =============================================================================
# Adult Finance Models (Poke)
# =============================================================================


class Transaction(Base):
    """Unified transaction model for adult finance - expenses, income, transfers."""

    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # 'expense' | 'income' | 'transfer'
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)  # Original amount in cents
    currency: Mapped[str] = mapped_column(String(3), nullable=False)  # ISO 4217 code
    amount_primary: Mapped[int] = mapped_column(
        BigInteger, nullable=False
    )  # Converted to user's primary currency
    exchange_rate: Mapped[Optional[float]] = mapped_column(
        Numeric(18, 8), nullable=True
    )  # Rate at transaction time
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    counterparty: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )  # Who paid/received
    transaction_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    recurring_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("recurring_transactions.id", ondelete="SET NULL"), nullable=True
    )
    tags: Mapped[dict] = mapped_column(JSONB, default=list)  # Array of tag strings
    extra_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User")
    recurring_source: Mapped[Optional["RecurringTransaction"]] = relationship(
        "RecurringTransaction", back_populates="generated_transactions"
    )

    __table_args__ = (
        Index("idx_transactions_user_date", "user_id", "transaction_date"),
        Index("idx_transactions_user_type", "user_id", "type"),
        Index("idx_transactions_user_category", "user_id", "category"),
    )


class Budget(Base):
    """Budget model - monthly spending limits per category."""

    __tablename__ = "budgets"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    monthly_limit: Mapped[int] = mapped_column(
        BigInteger, nullable=False
    )  # In cents (primary currency)
    alert_threshold: Mapped[int] = mapped_column(
        BigInteger, default=80
    )  # Percentage 0-100
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User")

    __table_args__ = (
        UniqueConstraint("user_id", "category", name="uq_budget_user_category"),
        Index("idx_budgets_user_active", "user_id", "is_active"),
    )


class Debt(Base):
    """Debt model - track money lent to or borrowed from others."""

    __tablename__ = "debts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    counterparty_name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'lent' | 'borrowed'
    original_amount: Mapped[int] = mapped_column(BigInteger, nullable=False)  # In cents
    remaining_amount: Mapped[int] = mapped_column(BigInteger, nullable=False)  # In cents
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    due_date: Mapped[Optional[datetime]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), default="active"
    )  # 'active' | 'paid' | 'forgiven'
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User")

    __table_args__ = (
        Index("idx_debts_user_status", "user_id", "status"),
    )


class RecurringTransaction(Base):
    """Recurring transaction template - subscriptions, regular income, bills."""

    __tablename__ = "recurring_transactions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)  # e.g., "Netflix", "Salary"
    template: Mapped[dict] = mapped_column(
        JSONB, nullable=False
    )  # {type, amount, currency, category, description, counterparty}
    frequency: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # 'daily' | 'weekly' | 'biweekly' | 'monthly' | 'yearly'
    next_due_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    last_processed_date: Mapped[Optional[datetime]] = mapped_column(Date, nullable=True)
    reminder_days_before: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User")
    generated_transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction", back_populates="recurring_source"
    )

    __table_args__ = (
        Index("idx_recurring_user_active", "user_id", "is_active"),
        Index("idx_recurring_next_due", "next_due_date", "is_active"),
    )


class ExchangeRate(Base):
    """Exchange rate history - for currency conversion."""

    __tablename__ = "exchange_rates"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    from_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    to_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    rate: Mapped[float] = mapped_column(Numeric(18, 8), nullable=False)
    date: Mapped[datetime] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("from_currency", "to_currency", "date", name="uq_exchange_rate"),
        Index("idx_exchange_rate_lookup", "from_currency", "to_currency", "date"),
    )
