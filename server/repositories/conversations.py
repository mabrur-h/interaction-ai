"""Conversation repository."""

import uuid
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.database.models import Conversation
from server.repositories.base import UserScopedRepository


class ConversationRepository(UserScopedRepository[Conversation]):
    """Repository for Conversation operations (user-scoped)."""

    model = Conversation

    async def get_or_create_default(self) -> Conversation:
        """Get the user's default conversation, creating if needed.

        Most users will have a single conversation. This method ensures
        one exists and returns it.

        Returns:
            The user's conversation
        """
        result = await self.session.execute(
            select(Conversation)
            .where(Conversation.user_id == self.user_id)
            .order_by(Conversation.created_at.desc())
            .limit(1)
        )
        conversation = result.scalar_one_or_none()

        if conversation is None:
            conversation = await self.create()

        return conversation

    async def get_latest(self) -> Optional[Conversation]:
        """Get the user's most recent conversation.

        Returns:
            The latest Conversation or None
        """
        result = await self.session.execute(
            select(Conversation)
            .where(Conversation.user_id == self.user_id)
            .order_by(Conversation.updated_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def delete_all_for_user(self) -> int:
        """Delete all conversations for the current user.

        This also deletes all messages due to cascade.

        Returns:
            Number of conversations deleted
        """
        conversations = await self.get_all(limit=1000)
        count = 0
        for conv in conversations:
            if await self.delete(conv.id):
                count += 1
        return count
