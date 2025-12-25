"""Reminder log repository for tracking sent payment reminders."""

from datetime import date
from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from server.database.models import ReminderLog
from server.repositories.base import UserScopedRepository


class ReminderLogRepository(UserScopedRepository[ReminderLog]):
    """Repository for ReminderLog operations (user-scoped)."""

    model = ReminderLog

    async def was_reminder_sent(
        self,
        recurring_id: int,
        reminder_date: date,
    ) -> bool:
        """Check if a reminder was already sent for this recurring transaction on this date.

        Args:
            recurring_id: The recurring transaction ID
            reminder_date: The date to check

        Returns:
            True if reminder was already sent
        """
        query = select(ReminderLog.id).where(
            and_(
                ReminderLog.user_id == self.user_id,
                ReminderLog.recurring_id == recurring_id,
                ReminderLog.reminder_date == reminder_date,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None

    async def log_reminder(
        self,
        recurring_id: int,
        reminder_date: date,
        due_date: date,
        channel: str = "in_app",
    ) -> ReminderLog:
        """Log that a reminder was sent.

        Args:
            recurring_id: The recurring transaction ID
            reminder_date: The date the reminder was sent
            due_date: The due date of the transaction
            channel: The channel used (in_app, email, push)

        Returns:
            The created ReminderLog
        """
        return await self.create(
            recurring_id=recurring_id,
            reminder_date=reminder_date,
            due_date=due_date,
            channel=channel,
        )

    async def get_recent_reminders(
        self,
        days: int = 7,
    ) -> Sequence[ReminderLog]:
        """Get reminders sent in the last N days.

        Args:
            days: Number of days to look back

        Returns:
            List of reminder logs
        """
        from datetime import timedelta

        start_date = date.today() - timedelta(days=days)
        query = (
            select(ReminderLog)
            .where(
                and_(
                    ReminderLog.user_id == self.user_id,
                    ReminderLog.reminder_date >= start_date,
                )
            )
            .order_by(ReminderLog.sent_at.desc())
        )
        result = await self.session.execute(query)
        return result.scalars().all()


# ==============================================================================
# Utility function for system-wide operations (not user-scoped)
# ==============================================================================


async def get_users_with_reminders_enabled(
    session: AsyncSession,
) -> Sequence:
    """Get all users who have reminders enabled.

    This is a system-level function for background task processing.

    Args:
        session: Database session

    Returns:
        List of User objects with reminders enabled
    """
    from server.database.models import User

    query = (
        select(User)
        .where(User.is_active == True)
        # Filter users with reminders enabled in notification_settings
        # JSONB query: notification_settings->>'reminders_enabled' = 'true'
        .where(
            User.notification_settings["reminders_enabled"].astext == "true"
        )
    )
    result = await session.execute(query)
    return result.scalars().all()
