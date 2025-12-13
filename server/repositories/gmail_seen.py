"""Gmail seen messages repository."""

import uuid
from typing import Sequence

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from server.database.models import GmailSeenMessage
from server.repositories.base import UserScopedRepository


class GmailSeenRepository(UserScopedRepository[GmailSeenMessage]):
    """Repository for Gmail seen message tracking (user-scoped)."""

    model = GmailSeenMessage

    async def is_seen(self, message_id: str) -> bool:
        """Check if a Gmail message has been seen.

        Args:
            message_id: Gmail message ID

        Returns:
            True if seen, False otherwise
        """
        result = await self.session.execute(
            select(GmailSeenMessage.id).where(
                GmailSeenMessage.user_id == self.user_id,
                GmailSeenMessage.message_id == message_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def mark_seen(self, message_id: str) -> GmailSeenMessage:
        """Mark a Gmail message as seen.

        Uses upsert to handle duplicates gracefully.

        Args:
            message_id: Gmail message ID

        Returns:
            The GmailSeenMessage record
        """
        # Use PostgreSQL upsert (INSERT ... ON CONFLICT DO NOTHING)
        stmt = insert(GmailSeenMessage).values(
            user_id=self.user_id,
            message_id=message_id,
        ).on_conflict_do_nothing(
            index_elements=["user_id", "message_id"]
        )
        await self.session.execute(stmt)
        await self.session.flush()

        # Get the record (either existing or newly created)
        result = await self.session.execute(
            select(GmailSeenMessage).where(
                GmailSeenMessage.user_id == self.user_id,
                GmailSeenMessage.message_id == message_id,
            )
        )
        return result.scalar_one()

    async def mark_many_seen(self, message_ids: Sequence[str]) -> int:
        """Mark multiple Gmail messages as seen.

        Args:
            message_ids: List of Gmail message IDs

        Returns:
            Number of new records created
        """
        if not message_ids:
            return 0

        count = 0
        for msg_id in message_ids:
            if not await self.is_seen(msg_id):
                await self.mark_seen(msg_id)
                count += 1
        return count

    async def get_seen_message_ids(self, limit: int = 300) -> Sequence[str]:
        """Get recently seen message IDs.

        Args:
            limit: Maximum number of IDs to return

        Returns:
            List of message IDs, most recent first
        """
        result = await self.session.execute(
            select(GmailSeenMessage.message_id)
            .where(GmailSeenMessage.user_id == self.user_id)
            .order_by(GmailSeenMessage.seen_at.desc())
            .limit(limit)
        )
        return [row[0] for row in result.fetchall()]

    async def cleanup_old_entries(self, keep_count: int = 300) -> int:
        """Remove old seen entries, keeping only the most recent.

        Args:
            keep_count: Number of recent entries to keep

        Returns:
            Number of entries deleted
        """
        # Get IDs to keep
        keep_result = await self.session.execute(
            select(GmailSeenMessage.id)
            .where(GmailSeenMessage.user_id == self.user_id)
            .order_by(GmailSeenMessage.seen_at.desc())
            .limit(keep_count)
        )
        keep_ids = {row[0] for row in keep_result.fetchall()}

        if not keep_ids:
            return 0

        # Delete entries not in keep list
        result = await self.session.execute(
            delete(GmailSeenMessage).where(
                GmailSeenMessage.user_id == self.user_id,
                ~GmailSeenMessage.id.in_(keep_ids),
            )
        )
        return result.rowcount
