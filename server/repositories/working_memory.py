"""Working memory repository."""

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from server.database.models import WorkingMemory
from server.repositories.base import UserScopedRepository


class WorkingMemoryRepository(UserScopedRepository[WorkingMemory]):
    """Repository for working memory operations (user-scoped).

    Each user has at most one working memory record containing
    their conversation summary.
    """

    model = WorkingMemory

    async def get_summary(self) -> Optional[str]:
        """Get the user's working memory summary.

        Returns:
            The summary text or None if not set
        """
        result = await self.session.execute(
            select(WorkingMemory.summary).where(
                WorkingMemory.user_id == self.user_id
            )
        )
        row = result.first()
        return row[0] if row else None

    async def get_or_create(self) -> WorkingMemory:
        """Get the user's working memory, creating if needed.

        Returns:
            The WorkingMemory record
        """
        result = await self.session.execute(
            select(WorkingMemory).where(WorkingMemory.user_id == self.user_id)
        )
        memory = result.scalar_one_or_none()

        if memory is None:
            memory = await self.create(summary="")

        return memory

    async def update_summary(self, summary: str) -> WorkingMemory:
        """Update or create the user's working memory summary.

        Args:
            summary: The new summary text

        Returns:
            The WorkingMemory record
        """
        # Use PostgreSQL upsert
        stmt = insert(WorkingMemory).values(
            user_id=self.user_id,
            summary=summary,
        ).on_conflict_do_update(
            index_elements=["user_id"],
            set_={"summary": summary},
        )
        await self.session.execute(stmt)
        await self.session.flush()

        result = await self.session.execute(
            select(WorkingMemory).where(WorkingMemory.user_id == self.user_id)
        )
        return result.scalar_one()

    async def clear(self) -> bool:
        """Clear the user's working memory.

        Returns:
            True if cleared, False if not found
        """
        result = await self.session.execute(
            select(WorkingMemory).where(WorkingMemory.user_id == self.user_id)
        )
        memory = result.scalar_one_or_none()

        if memory is None:
            return False

        return await self.delete(memory.id)

    async def append_to_summary(self, text: str) -> WorkingMemory:
        """Append text to the existing summary.

        Args:
            text: Text to append

        Returns:
            The updated WorkingMemory
        """
        current = await self.get_summary()
        if current:
            new_summary = f"{current}\n{text}"
        else:
            new_summary = text

        return await self.update_summary(new_summary)
