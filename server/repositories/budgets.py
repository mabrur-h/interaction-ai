"""Budget repository for adult finance."""

from typing import Dict, Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.database.models import Budget
from server.repositories.base import UserScopedRepository


class BudgetRepository(UserScopedRepository[Budget]):
    """Repository for Budget operations (user-scoped)."""

    model = Budget

    async def get_by_category(self, category: str) -> Optional[Budget]:
        """Get budget for a specific category.

        Args:
            category: The category name

        Returns:
            Budget or None if not found
        """
        query = select(Budget).where(
            Budget.user_id == self.user_id,
            Budget.category == category,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_active_budgets(self) -> Sequence[Budget]:
        """Get all active budgets for the user.

        Returns:
            List of active budgets
        """
        query = (
            select(Budget)
            .where(
                Budget.user_id == self.user_id,
                Budget.is_active == True,
            )
            .order_by(Budget.category)
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def set_budget(
        self,
        category: str,
        monthly_limit: int,
        alert_threshold: int = 80,
    ) -> Budget:
        """Set or update a budget for a category.

        Args:
            category: The category name
            monthly_limit: Monthly limit in cents
            alert_threshold: Alert when this percentage is reached

        Returns:
            The created or updated budget
        """
        existing = await self.get_by_category(category)
        if existing:
            return await self.update(
                existing.id,
                monthly_limit=monthly_limit,
                alert_threshold=alert_threshold,
                is_active=True,
            )
        return await self.create(
            category=category,
            monthly_limit=monthly_limit,
            alert_threshold=alert_threshold,
        )

    async def deactivate(self, category: str) -> bool:
        """Deactivate a budget (soft delete).

        Args:
            category: The category name

        Returns:
            True if deactivated, False if not found
        """
        existing = await self.get_by_category(category)
        if not existing:
            return False
        await self.update(existing.id, is_active=False)
        return True

    async def get_all_limits(self) -> Dict[str, int]:
        """Get all active budget limits as a dict.

        Returns:
            Dict of category -> monthly_limit
        """
        budgets = await self.get_active_budgets()
        return {b.category: b.monthly_limit for b in budgets}
