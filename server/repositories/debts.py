"""Debt repository for adult finance."""

from typing import Dict, Optional, Sequence

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from server.database.models import Debt
from server.repositories.base import UserScopedRepository


class DebtRepository(UserScopedRepository[Debt]):
    """Repository for Debt operations (user-scoped)."""

    model = Debt

    async def get_active_debts(
        self,
        debt_type: Optional[str] = None,
    ) -> Sequence[Debt]:
        """Get all active debts.

        Args:
            debt_type: Optional filter by 'lent' or 'borrowed'

        Returns:
            List of active debts
        """
        query = (
            select(Debt)
            .where(
                Debt.user_id == self.user_id,
                Debt.status == "active",
            )
            .order_by(Debt.due_date.asc().nullslast(), Debt.created_at.desc())
        )

        if debt_type:
            query = query.where(Debt.type == debt_type)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_counterparty(
        self,
        counterparty_name: str,
        status: str = "active",
    ) -> Sequence[Debt]:
        """Get debts with a specific counterparty.

        Args:
            counterparty_name: Name of the person
            status: Filter by status

        Returns:
            List of debts
        """
        query = (
            select(Debt)
            .where(
                Debt.user_id == self.user_id,
                Debt.counterparty_name.ilike(f"%{counterparty_name}%"),
                Debt.status == status,
            )
            .order_by(Debt.created_at.desc())
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def record_payment(
        self,
        debt_id: int,
        payment_amount: int,
    ) -> Optional[Debt]:
        """Record a payment toward a debt.

        Args:
            debt_id: The debt ID
            payment_amount: Amount paid in cents

        Returns:
            Updated debt or None if not found
        """
        debt = await self.get_by_id(debt_id)
        if not debt:
            return None

        new_remaining = max(0, debt.remaining_amount - payment_amount)
        new_status = "paid" if new_remaining == 0 else "active"

        return await self.update(
            debt_id,
            remaining_amount=new_remaining,
            status=new_status,
        )

    async def forgive(self, debt_id: int) -> Optional[Debt]:
        """Mark a debt as forgiven.

        Args:
            debt_id: The debt ID

        Returns:
            Updated debt or None if not found
        """
        return await self.update(
            debt_id,
            remaining_amount=0,
            status="forgiven",
        )

    async def get_summary(self) -> Dict[str, int]:
        """Get debt summary (total lent, borrowed, net).

        Returns:
            Dict with 'total_lent', 'total_borrowed', 'net_position'
        """
        query = (
            select(
                Debt.type,
                func.sum(Debt.remaining_amount).label("total"),
            )
            .where(
                Debt.user_id == self.user_id,
                Debt.status == "active",
            )
            .group_by(Debt.type)
        )

        result = await self.session.execute(query)
        totals = {row.type: row.total or 0 for row in result.all()}

        total_lent = totals.get("lent", 0)
        total_borrowed = totals.get("borrowed", 0)

        return {
            "total_lent": total_lent,
            "total_borrowed": total_borrowed,
            "net_position": total_lent - total_borrowed,
        }

    async def get_overdue(self) -> Sequence[Debt]:
        """Get debts that are past due date.

        Returns:
            List of overdue debts
        """
        from datetime import date

        query = (
            select(Debt)
            .where(
                Debt.user_id == self.user_id,
                Debt.status == "active",
                Debt.due_date < date.today(),
            )
            .order_by(Debt.due_date.asc())
        )
        result = await self.session.execute(query)
        return result.scalars().all()
