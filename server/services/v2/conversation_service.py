"""Async conversation service using PostgreSQL repositories."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Sequence

from server.database.models import Conversation, Message
from server.logging_config import logger
from server.models import ChatMessage
from server.repositories.conversations import ConversationRepository
from server.repositories.messages import MessageRepository
from server.repositories.working_memory import WorkingMemoryRepository


class ConversationService:
    """High-level async conversation management.

    This is the v2 async version that uses PostgreSQL repositories
    instead of file-based storage.
    """

    def __init__(
        self,
        conversation_repo: ConversationRepository,
        working_memory_repo: WorkingMemoryRepository,
    ):
        """Initialize with repositories.

        Args:
            conversation_repo: ConversationRepository instance (user-scoped)
            working_memory_repo: WorkingMemoryRepository instance (user-scoped)
        """
        self._conv_repo = conversation_repo
        self._wm_repo = working_memory_repo
        self._message_repo: Optional[MessageRepository] = None
        self._conversation: Optional[Conversation] = None

    async def _ensure_conversation(self) -> Conversation:
        """Ensure we have an active conversation.

        Returns:
            The current conversation
        """
        if self._conversation is None:
            self._conversation = await self._conv_repo.get_or_create_default()
        return self._conversation

    async def _get_message_repo(self) -> MessageRepository:
        """Get or create the message repository for the current conversation.

        Returns:
            MessageRepository for the current conversation
        """
        if self._message_repo is None:
            conversation = await self._ensure_conversation()
            self._message_repo = MessageRepository(
                self._conv_repo.session, conversation.id
            )
        return self._message_repo

    async def record_user_message(self, content: str) -> Message:
        """Record a user message.

        Args:
            content: The message content

        Returns:
            The created Message
        """
        msg_repo = await self._get_message_repo()
        message = await msg_repo.add_user_message(content)

        # Update working memory
        await self._wm_repo.append_to_summary(
            f"[{message.created_at.strftime('%Y-%m-%d %H:%M:%S')}] User: {content[:200]}..."
            if len(content) > 200
            else f"[{message.created_at.strftime('%Y-%m-%d %H:%M:%S')}] User: {content}"
        )

        return message

    async def record_agent_message(self, content: str, agent_name: Optional[str] = None) -> Message:
        """Record an agent notification message.

        Args:
            content: The message content
            agent_name: Optional agent name

        Returns:
            The created Message
        """
        msg_repo = await self._get_message_repo()
        message = await msg_repo.add_agent_message(content, agent_name)

        # Update working memory
        prefix = f"Agent ({agent_name})" if agent_name else "Agent"
        await self._wm_repo.append_to_summary(
            f"[{message.created_at.strftime('%Y-%m-%d %H:%M:%S')}] {prefix}: {content[:200]}..."
            if len(content) > 200
            else f"[{message.created_at.strftime('%Y-%m-%d %H:%M:%S')}] {prefix}: {content}"
        )

        return message

    async def record_reply(self, content: str) -> Message:
        """Record an assistant reply.

        Args:
            content: The reply content

        Returns:
            The created Message
        """
        msg_repo = await self._get_message_repo()
        message = await msg_repo.add_assistant_message(content)

        # Update working memory
        await self._wm_repo.append_to_summary(
            f"[{message.created_at.strftime('%Y-%m-%d %H:%M:%S')}] Poke: {content[:200]}..."
            if len(content) > 200
            else f"[{message.created_at.strftime('%Y-%m-%d %H:%M:%S')}] Poke: {content}"
        )

        return message

    async def record_wait(self, reason: str) -> Message:
        """Record a wait marker (internal orchestration, not shown to user).

        Args:
            reason: The wait reason

        Returns:
            The created Message
        """
        msg_repo = await self._get_message_repo()
        # Store as agent message with special extra_data
        message = await msg_repo.add_message(
            role="system", content=reason, extra_data={"type": "wait"}
        )
        return message

    async def get_messages(self, limit: int = 100) -> Sequence[Message]:
        """Get conversation messages.

        Args:
            limit: Maximum number of messages

        Returns:
            List of Messages
        """
        msg_repo = await self._get_message_repo()
        return await msg_repo.get_recent_messages(limit)

    async def to_chat_messages(self) -> List[ChatMessage]:
        """Convert conversation to ChatMessage format for API responses.

        Returns:
            List of ChatMessage objects
        """
        messages = await self.get_messages(limit=1000)
        chat_messages: List[ChatMessage] = []

        for msg in messages:
            # Skip wait/system markers
            if msg.role == "system":
                continue

            timestamp = msg.created_at.strftime("%Y-%m-%d %H:%M:%S") if msg.created_at else None

            if msg.role == "user":
                chat_messages.append(
                    ChatMessage(role="user", content=msg.content, timestamp=timestamp)
                )
            elif msg.role == "assistant":
                chat_messages.append(
                    ChatMessage(role="assistant", content=msg.content, timestamp=timestamp)
                )
            elif msg.role == "agent":
                # Agent messages can be shown as assistant messages with agent context
                chat_messages.append(
                    ChatMessage(role="assistant", content=msg.content, timestamp=timestamp)
                )

        return chat_messages

    async def load_transcript(self) -> str:
        """Load the conversation as a transcript string.

        Returns:
            Formatted transcript
        """
        msg_repo = await self._get_message_repo()
        return await msg_repo.get_formatted_history(limit=500)

    async def get_working_memory_summary(self) -> Optional[str]:
        """Get the working memory summary.

        Returns:
            The summary or None
        """
        return await self._wm_repo.get_summary()

    async def clear(self) -> None:
        """Clear all conversation data for the user."""
        # Delete all conversations (cascades to messages)
        await self._conv_repo.delete_all_for_user()

        # Clear working memory
        await self._wm_repo.clear()

        # Reset local state
        self._conversation = None
        self._message_repo = None


__all__ = ["ConversationService"]
