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

    # Adult finance fields
    primary_currency: Mapped[str] = mapped_column(String(3), default="UZS")  # ISO 4217 code
    currency_settings: Mapped[dict] = mapped_column(
        JSONB, default=dict
    )  # {display_currencies: [], auto_convert: bool}
    notification_settings: Mapped[dict] = mapped_column(
        JSONB,
        default=lambda: {
            "reminders_enabled": True,
            "reminder_time": "09:00",
            "channels": ["in_app"],
        },
    )  # {reminders_enabled: bool, reminder_time: "HH:MM", channels: ["in_app", "email"]}

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


class ReminderLog(Base):
    """Reminder log - tracks sent payment reminders to prevent duplicates."""

    __tablename__ = "reminder_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    recurring_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("recurring_transactions.id", ondelete="CASCADE"),
        nullable=False,
    )
    reminder_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    due_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    channel: Mapped[str] = mapped_column(String(20), default="in_app")

    # Relationships
    user: Mapped["User"] = relationship("User")
    recurring_transaction: Mapped["RecurringTransaction"] = relationship(
        "RecurringTransaction"
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id", "recurring_id", "reminder_date", name="uq_reminder_log"
        ),
        Index("idx_reminder_logs_user_date", "user_id", "reminder_date"),
    )


class QuickReminder(Base):
    """Quick reminder - short-term reminders (minutes/hours) via Celery ETA."""

    __tablename__ = "quick_reminders"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    message: Mapped[str] = mapped_column(String(500), nullable=False)
    amount: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)  # Optional amount
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    remind_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    celery_task_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), default="pending"
    )  # 'pending', 'sent', 'cancelled'
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User")

    __table_args__ = (
        Index("idx_quick_reminders_user_status", "user_id", "status"),
        Index("idx_quick_reminders_remind_at", "remind_at"),
    )
