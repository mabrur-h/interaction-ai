"""Message repository."""

import uuid
from typing import Optional, Sequence

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from server.database.models import Message, Conversation
from server.repositories.base import BaseRepository


class MessageRepository(BaseRepository[Message]):
    """Repository for Message operations.

    Messages are scoped by conversation, not directly by user.
    The conversation itself is user-scoped.
    """

    model = Message

    def __init__(self, session: AsyncSession, conversation_id: uuid.UUID):
        """Initialize with session and conversation ID.

        Args:
            session: SQLAlchemy async session
            conversation_id: The conversation's UUID
        """
        super().__init__(session)
        self.conversation_id = conversation_id

    async def get_messages(
        self, limit: int = 100, offset: int = 0
    ) -> Sequence[Message]:
        """Get messages for the conversation.

        Args:
            limit: Maximum number of messages
            offset: Number of messages to skip

        Returns:
            List of Messages, ordered by creation time
        """
        result = await self.session.execute(
            select(Message)
            .where(Message.conversation_id == self.conversation_id)
            .order_by(Message.created_at)
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def get_recent_messages(self, limit: int = 50) -> Sequence[Message]:
        """Get the most recent messages.

        Args:
            limit: Number of recent messages to get

        Returns:
            List of Messages, ordered by creation time (oldest first)
        """
        # Subquery to get IDs of recent messages
        result = await self.session.execute(
            select(Message)
            .where(Message.conversation_id == self.conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        messages = list(result.scalars().all())
        # Reverse to get oldest first
        messages.reverse()
        return messages

    async def add_message(
        self,
        role: str,
        content: str,
        extra_data: Optional[dict] = None,
    ) -> Message:
        """Add a new message to the conversation.

        Args:
            role: Message role ('user', 'assistant', 'agent')
            content: Message content
            extra_data: Optional extra data

        Returns:
            The created Message
        """
        return await self.create(
            conversation_id=self.conversation_id,
            role=role,
            content=content,
            extra_data=extra_data or {},
        )

    async def add_user_message(self, content: str) -> Message:
        """Add a user message.

        Args:
            content: Message content

        Returns:
            The created Message
        """
        return await self.add_message("user", content)

    async def add_assistant_message(self, content: str) -> Message:
        """Add an assistant message.

        Args:
            content: Message content

        Returns:
            The created Message
        """
        return await self.add_message("assistant", content)

    async def add_agent_message(
        self, content: str, agent_name: Optional[str] = None
    ) -> Message:
        """Add an agent notification message.

        Args:
            content: Message content
            agent_name: Optional agent name for extra_data

        Returns:
            The created Message
        """
        extra_data = {"agent_name": agent_name} if agent_name else {}
        return await self.add_message("agent", content, extra_data)

    async def count_messages(self) -> int:
        """Count total messages in the conversation.

        Returns:
            Number of messages
        """
        result = await self.session.execute(
            select(func.count(Message.id)).where(
                Message.conversation_id == self.conversation_id
            )
        )
        return result.scalar() or 0

    async def get_formatted_history(self, limit: int = 100) -> str:
        """Get conversation history as formatted text.

        Args:
            limit: Maximum number of messages

        Returns:
            Formatted conversation string
        """
        messages = await self.get_recent_messages(limit)
        lines = []
        for msg in messages:
            prefix = {
                "user": "User",
                "assistant": "Assistant",
                "agent": "Agent",
            }.get(msg.role, msg.role.title())
            lines.append(f"{prefix}: {msg.content}")
        return "\n\n".join(lines)
