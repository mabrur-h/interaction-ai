"""Savings goals repository for Wally Junior."""

import uuid
from datetime import datetime
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.database.models import SavingsGoal
from server.repositories.base import UserScopedRepository


class SavingsGoalRepository(UserScopedRepository[SavingsGoal]):
    """Repository for SavingsGoal operations (user-scoped)."""

    model = SavingsGoal

    async def create_goal(
        self,
        name: str,
        target_amount: int,
        emoji: Optional[str] = None,
    ) -> SavingsGoal:
        """Create a new savings goal.

        Args:
            name: Goal name (e.g., "New Bike")
            target_amount: Target amount in cents
            emoji: Optional emoji for the goal

        Returns:
            The created SavingsGoal
        """
        return await self.create(
            name=name,
            target_amount=target_amount,
            current_amount=0,
            status="active",
            emoji=emoji,
        )

    async def get_active_goals(self) -> Sequence[SavingsGoal]:
        """Get all active savings goals for the user.

        Returns:
            List of active SavingsGoals
        """
        result = await self.session.execute(
            select(SavingsGoal)
            .where(
                SavingsGoal.user_id == self.user_id,
                SavingsGoal.status == "active",
            )
            .order_by(SavingsGoal.created_at.desc())
        )
        return result.scalars().all()

    async def get_all_goals(self, include_completed: bool = True) -> Sequence[SavingsGoal]:
        """Get all savings goals for the user.

        Args:
            include_completed: Whether to include completed goals

        Returns:
            List of SavingsGoals
        """
        query = select(SavingsGoal).where(SavingsGoal.user_id == self.user_id)

        if not include_completed:
            query = query.where(SavingsGoal.status == "active")

        query = query.order_by(SavingsGoal.created_at.desc())
        result = await self.session.execute(query)
        return result.scalars().all()

    async def add_to_goal(self, goal_id: int, amount: int) -> Optional[SavingsGoal]:
        """Add money to a savings goal.

        Args:
            goal_id: The goal ID
            amount: Amount to add in cents

        Returns:
            The updated SavingsGoal or None if not found
        """
        goal = await self.get_by_id(goal_id)
        if not goal:
            return None

        new_amount = goal.current_amount + amount
        updates = {"current_amount": new_amount}

        # Check if goal is completed
        if new_amount >= goal.target_amount:
            updates["status"] = "completed"
            updates["completed_at"] = datetime.utcnow()

        return await self.update(goal_id, **updates)

    async def withdraw_from_goal(self, goal_id: int, amount: int) -> Optional[SavingsGoal]:
        """Withdraw money from a savings goal.

        Args:
            goal_id: The goal ID
            amount: Amount to withdraw in cents

        Returns:
            The updated SavingsGoal or None if not found
        """
        goal = await self.get_by_id(goal_id)
        if not goal:
            return None

        new_amount = max(0, goal.current_amount - amount)
        updates = {"current_amount": new_amount}

        # If goal was completed and now isn't, reactivate it
        if goal.status == "completed" and new_amount < goal.target_amount:
            updates["status"] = "active"
            updates["completed_at"] = None

        return await self.update(goal_id, **updates)

    async def abandon_goal(self, goal_id: int) -> Optional[SavingsGoal]:
        """Mark a goal as abandoned.

        Args:
            goal_id: The goal ID

        Returns:
            The updated SavingsGoal or None if not found
        """
        return await self.update(goal_id, status="abandoned")

    async def reactivate_goal(self, goal_id: int) -> Optional[SavingsGoal]:
        """Reactivate a goal.

        Args:
            goal_id: The goal ID

        Returns:
            The updated SavingsGoal or None if not found
        """
        goal = await self.get_by_id(goal_id)
        if not goal:
            return None

        updates = {"status": "active", "completed_at": None}
        return await self.update(goal_id, **updates)
