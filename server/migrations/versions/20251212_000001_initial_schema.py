"""Initial database schema.

Revision ID: 001
Revises: None
Create Date: 2024-12-12

This migration creates all tables for the OpenPoke application:
- users: Central user identity
- sessions: JWT refresh token tracking
- oauth_connections: Composio integrations (Gmail, Calendar)
- triggers: Scheduled tasks
- conversations: Chat sessions
- messages: Individual chat messages
- gmail_seen_messages: Processed email tracking
- execution_logs: Agent execution history
- agent_roster: Registered agents per user
- working_memory: Conversation summaries
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable UUID extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # Users table
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("google_id", sa.String(255), unique=True, nullable=False),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("display_name", sa.String(255), nullable=True),
        sa.Column("avatar_url", sa.Text, nullable=True),
        sa.Column("timezone", sa.String(100), server_default="UTC"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
        ),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean, server_default="true"),
    )

    # Sessions table
    op.create_table(
        "sessions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("refresh_token_hash", sa.String(255), unique=True, nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
        ),
        sa.Column("user_agent", sa.Text, nullable=True),
        sa.Column("ip_address", postgresql.INET, nullable=True),
    )
    op.create_index("idx_sessions_user_id", "sessions", ["user_id"])

    # OAuth connections table
    op.create_table(
        "oauth_connections",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("composio_user_id", sa.String(255), nullable=False),
        sa.Column("composio_connection_id", sa.String(255), nullable=True),
        sa.Column("provider_email", sa.String(255), nullable=True),
        sa.Column("status", sa.String(50), server_default="pending"),
        sa.Column("extra_data", postgresql.JSONB, server_default="{}"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
        ),
        sa.UniqueConstraint("user_id", "provider", name="uq_oauth_user_provider"),
    )

    # Triggers table
    op.create_table(
        "triggers",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("agent_name", sa.String(255), nullable=False),
        sa.Column("payload", sa.Text, nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_trigger", sa.DateTime(timezone=True), nullable=True),
        sa.Column("recurrence_rule", sa.Text, nullable=True),
        sa.Column("timezone", sa.String(100), nullable=True),
        sa.Column("status", sa.String(50), server_default="active"),
        sa.Column("last_error", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
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

    # Conversations table
    op.create_table(
        "conversations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index("idx_conversations_user", "conversations", ["user_id"])

    # Messages table
    op.create_table(
        "messages",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column(
            "conversation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("extra_data", postgresql.JSONB, server_default="{}"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index(
        "idx_messages_conv_time", "messages", ["conversation_id", "created_at"]
    )

    # Gmail seen messages table
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
        sa.Column(
            "seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
        ),
        sa.UniqueConstraint(
            "user_id", "message_id", name="uq_gmail_seen_user_message"
        ),
    )

    # Execution logs table
    op.create_table(
        "execution_logs",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("agent_name", sa.String(255), nullable=False),
        sa.Column("tag", sa.String(50), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index(
        "idx_exec_logs_user_agent",
        "execution_logs",
        ["user_id", "agent_name", "created_at"],
    )

    # Agent roster table
    op.create_table(
        "agent_roster",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("agent_name", sa.String(255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
        ),
        sa.UniqueConstraint(
            "user_id", "agent_name", name="uq_agent_roster_user_agent"
        ),
    )

    # Working memory table
    op.create_table(
        "working_memory",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("summary", sa.Text, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index(
        "idx_working_memory_user", "working_memory", ["user_id"], unique=True
    )


def downgrade() -> None:
    op.drop_table("working_memory")
    op.drop_table("agent_roster")
    op.drop_table("execution_logs")
    op.drop_table("gmail_seen_messages")
    op.drop_table("messages")
    op.drop_table("conversations")
    op.drop_table("triggers")
    op.drop_table("oauth_connections")
    op.drop_table("sessions")
    op.drop_table("users")
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
