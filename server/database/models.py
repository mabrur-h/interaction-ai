"""SQLAlchemy ORM models for OpenPoke."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
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
    google_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
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

    # Relationships
    sessions: Mapped[list["Session"]] = relationship(
        "Session", back_populates="user", cascade="all, delete-orphan"
    )
    oauth_connections: Mapped[list["OAuthConnection"]] = relationship(
        "OAuthConnection", back_populates="user", cascade="all, delete-orphan"
    )
    triggers: Mapped[list["Trigger"]] = relationship(
        "Trigger", back_populates="user", cascade="all, delete-orphan"
    )
    conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation", back_populates="user", cascade="all, delete-orphan"
    )
    gmail_seen_messages: Mapped[list["GmailSeenMessage"]] = relationship(
        "GmailSeenMessage", back_populates="user", cascade="all, delete-orphan"
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


class Trigger(Base):
    """Trigger model - scheduled tasks."""

    __tablename__ = "triggers"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    agent_name: Mapped[str] = mapped_column(String(255), nullable=False)
    payload: Mapped[str] = mapped_column(Text, nullable=False)
    start_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    next_trigger: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    recurrence_rule: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    timezone: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="active")
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="triggers")

    __table_args__ = (
        Index(
            "idx_triggers_due",
            "status",
            "next_trigger",
            postgresql_where=(status == "active"),
        ),
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


class GmailSeenMessage(Base):
    """Gmail seen message model - tracks processed emails."""

    __tablename__ = "gmail_seen_messages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    message_id: Mapped[str] = mapped_column(String(255), nullable=False)
    seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="gmail_seen_messages")

    __table_args__ = (
        UniqueConstraint("user_id", "message_id", name="uq_gmail_seen_user_message"),
    )


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
