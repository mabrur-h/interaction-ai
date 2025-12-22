"""Recurring transaction repository for adult finance."""

from datetime import date, timedelta
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.database.models import RecurringTransaction
from server.repositories.base import UserScopedRepository


class RecurringTransactionRepository(UserScopedRepository[RecurringTransaction]):
    """Repository for RecurringTransaction operations (user-scoped)."""

    model = RecurringTransaction

    async def get_active(self) -> Sequence[RecurringTransaction]:
        """Get all active recurring transactions.

        Returns:
            List of active recurring transactions
        """
        query = (
            select(RecurringTransaction)
            .where(
                RecurringTransaction.user_id == self.user_id,
                RecurringTransaction.is_active == True,
            )
            .order_by(RecurringTransaction.next_due_date.asc())
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_due_today(self) -> Sequence[RecurringTransaction]:
        """Get recurring transactions due today.

        Returns:
            List of transactions due today
        """
        today = date.today()
        query = (
            select(RecurringTransaction)
            .where(
                RecurringTransaction.user_id == self.user_id,
                RecurringTransaction.is_active == True,
                RecurringTransaction.next_due_date <= today,
            )
            .order_by(RecurringTransaction.next_due_date.asc())
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_upcoming(self, days: int = 7) -> Sequence[RecurringTransaction]:
        """Get recurring transactions due in the next N days.

        Args:
            days: Number of days to look ahead

        Returns:
            List of upcoming transactions
        """
        today = date.today()
        end_date = today + timedelta(days=days)

        query = (
            select(RecurringTransaction)
            .where(
                RecurringTransaction.user_id == self.user_id,
                RecurringTransaction.is_active == True,
                RecurringTransaction.next_due_date <= end_date,
            )
            .order_by(RecurringTransaction.next_due_date.asc())
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def mark_processed(
        self,
        recurring_id: int,
        next_due: date,
    ) -> Optional[RecurringTransaction]:
        """Mark a recurring transaction as processed and set next due date.

        Args:
            recurring_id: The recurring transaction ID
            next_due: The next due date

        Returns:
            Updated recurring transaction
        """
        return await self.update(
            recurring_id,
            last_processed_date=date.today(),
            next_due_date=next_due,
        )

    async def pause(self, recurring_id: int) -> Optional[RecurringTransaction]:
        """Pause a recurring transaction.

        Args:
            recurring_id: The recurring transaction ID

        Returns:
            Updated recurring transaction
        """
        return await self.update(recurring_id, is_active=False)

    async def resume(self, recurring_id: int) -> Optional[RecurringTransaction]:
        """Resume a paused recurring transaction.

        Args:
            recurring_id: The recurring transaction ID

        Returns:
            Updated recurring transaction
        """
        return await self.update(recurring_id, is_active=True)

    async def get_monthly_total(self, transaction_type: str = "expense") -> int:
        """Calculate total monthly cost of recurring transactions.

        Args:
            transaction_type: Filter by type (expense/income)

        Returns:
            Total monthly cost in cents (normalized)
        """
        recurring = await self.get_active()
        total = 0

        frequency_multipliers = {
            "daily": 30,
            "weekly": 4.33,
            "biweekly": 2.17,
            "monthly": 1,
            "yearly": 1 / 12,
        }

        for r in recurring:
            template = r.template or {}
            if template.get("type") == transaction_type:
                amount = template.get("amount", 0)
                multiplier = frequency_multipliers.get(r.frequency, 1)
                total += int(amount * multiplier)

        return total
