"""Quick reminder repository for short-term reminders."""

from datetime import datetime
from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import select

from server.database.models import QuickReminder
from server.repositories.base import UserScopedRepository


class QuickReminderRepository(UserScopedRepository[QuickReminder]):
    """Repository for QuickReminder operations (user-scoped)."""

    model = QuickReminder

    async def get_pending(self) -> Sequence[QuickReminder]:
        """Get all pending reminders for the user.

        Returns:
            List of pending quick reminders
        """
        query = (
            select(QuickReminder)
            .where(
                QuickReminder.user_id == self.user_id,
                QuickReminder.status == "pending",
            )
            .order_by(QuickReminder.remind_at.asc())
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_celery_task_id(self, task_id: str) -> Optional[QuickReminder]:
        """Get a reminder by its Celery task ID.

        Args:
            task_id: The Celery task ID

        Returns:
            The reminder or None if not found
        """
        query = select(QuickReminder).where(
            QuickReminder.user_id == self.user_id,
            QuickReminder.celery_task_id == task_id,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def mark_sent(self, reminder_id: int) -> Optional[QuickReminder]:
        """Mark a reminder as sent.

        Args:
            reminder_id: The reminder ID

        Returns:
            Updated reminder
        """
        return await self.update(
            reminder_id,
            status="sent",
            sent_at=datetime.utcnow(),
        )

    async def cancel(self, reminder_id: int) -> Optional[QuickReminder]:
        """Cancel a pending reminder.

        Args:
            reminder_id: The reminder ID

        Returns:
            Updated reminder or None if not found
        """
        reminder = await self.get_by_id(reminder_id)
        if reminder and reminder.status == "pending":
            return await self.update(reminder_id, status="cancelled")
        return reminder


# ==============================================================================
# Utility function for system-wide operations (not user-scoped)
# ==============================================================================


async def get_reminder_by_id_system(
    session,
    reminder_id: int,
) -> Optional[QuickReminder]:
    """Get a reminder by ID without user scoping (for Celery tasks).

    Args:
        session: Database session
        reminder_id: The reminder ID

    Returns:
        The reminder or None
    """
    query = select(QuickReminder).where(QuickReminder.id == reminder_id)
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def mark_reminder_sent_system(
    session,
    reminder_id: int,
) -> bool:
    """Mark a reminder as sent (for Celery tasks).

    Args:
        session: Database session
        reminder_id: The reminder ID

    Returns:
        True if updated, False otherwise
    """
    from sqlalchemy import update

    result = await session.execute(
        update(QuickReminder)
        .where(QuickReminder.id == reminder_id)
        .values(status="sent", sent_at=datetime.utcnow())
    )
    return result.rowcount > 0
