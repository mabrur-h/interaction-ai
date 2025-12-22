"""Finance service for Wally Junior - expense tracking and savings goals."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Sequence

from server.database.models import Expense, SavingsGoal, User
from server.repositories.expenses import ExpenseRepository
from server.repositories.savings_goals import SavingsGoalRepository


class FinanceService:
    """High-level finance management for kids.

    Handles expense tracking, balance calculations, and savings goals.
    All amounts are in cents to avoid floating-point issues.
    """

    def __init__(
        self,
        expense_repo: ExpenseRepository,
        savings_repo: SavingsGoalRepository,
        user: User,
        auto_commit: bool = True,
    ):
        """Initialize with repositories.

        Args:
            expense_repo: ExpenseRepository instance (user-scoped)
            savings_repo: SavingsGoalRepository instance (user-scoped)
            user: The User model instance
            auto_commit: If True, commit after each operation
        """
        self._expense_repo = expense_repo
        self._savings_repo = savings_repo
        self._user = user
        self._auto_commit = auto_commit

    @property
    def session(self):
        """Get the underlying database session."""
        return self._expense_repo.session

    # =========================================================================
    # Expense Tracking
    # =========================================================================

    async def log_expense(
        self,
        amount_cents: int,
        category: str,
        description: Optional[str] = None,
        expense_date: Optional[datetime] = None,
    ) -> Expense:
        """Log a new expense.

        Args:
            amount_cents: Amount in cents
            category: Expense category (food, toys, games, etc.)
            description: Optional description of the purchase
            expense_date: When the expense occurred (defaults to now)

        Returns:
            The created Expense
        """
        expense = await self._expense_repo.log_expense(
            amount=amount_cents,
            category=category,
            description=description,
            expense_date=expense_date,
        )

        if self._auto_commit:
            await self.session.commit()

        return expense

    async def get_expenses(
        self,
        limit: int = 50,
        category: Optional[str] = None,
        period: Optional[str] = None,
    ) -> Sequence[Expense]:
        """Get expenses with optional filters.

        Args:
            limit: Maximum number of results
            category: Optional category filter
            period: Optional period filter (today, week, month, all)

        Returns:
            List of Expenses
        """
        start_date = None
        if period == "today":
            start_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "week":
            start_date = datetime.utcnow() - timedelta(days=7)
        elif period == "month":
            start_date = datetime.utcnow() - timedelta(days=30)

        return await self._expense_repo.get_expenses(
            limit=limit,
            category=category,
            start_date=start_date,
        )

    async def get_balance(self) -> int:
        """Get current balance (initial_balance - total_spent).

        Returns:
            Balance in cents
        """
        total_spent = await self._expense_repo.get_total_spent()
        return self._user.initial_balance - total_spent

    async def get_spending_summary(self, period: str = "all") -> Dict:
        """Get spending summary for a period.

        Args:
            period: Time period (today, week, month, all)

        Returns:
            Dictionary with spending stats
        """
        start_date = None
        if period == "today":
            start_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "week":
            start_date = datetime.utcnow() - timedelta(days=7)
        elif period == "month":
            start_date = datetime.utcnow() - timedelta(days=30)

        total = await self._expense_repo.get_total_spent(start_date=start_date)
        by_category = await self._expense_repo.get_spending_by_category(start_date=start_date)
        count = await self._expense_repo.get_expense_count(start_date=start_date)

        return {
            "total_cents": total,
            "by_category": by_category,
            "count": count,
            "period": period,
        }

    # =========================================================================
    # Savings Goals
    # =========================================================================

    async def create_savings_goal(
        self,
        name: str,
        target_amount_cents: int,
        emoji: Optional[str] = None,
    ) -> SavingsGoal:
        """Create a new savings goal.

        Args:
            name: Goal name (e.g., "New Bike")
            target_amount_cents: Target amount in cents
            emoji: Optional emoji for the goal

        Returns:
            The created SavingsGoal
        """
        goal = await self._savings_repo.create_goal(
            name=name,
            target_amount=target_amount_cents,
            emoji=emoji,
        )

        if self._auto_commit:
            await self.session.commit()

        return goal

    async def add_to_savings(self, goal_id: int, amount_cents: int) -> Optional[SavingsGoal]:
        """Add money to a savings goal.

        Args:
            goal_id: The goal ID
            amount_cents: Amount to add in cents

        Returns:
            The updated SavingsGoal or None if not found
        """
        goal = await self._savings_repo.add_to_goal(goal_id, amount_cents)

        if goal and self._auto_commit:
            await self.session.commit()

        return goal

    async def withdraw_from_savings(self, goal_id: int, amount_cents: int) -> Optional[SavingsGoal]:
        """Withdraw money from a savings goal.

        Args:
            goal_id: The goal ID
            amount_cents: Amount to withdraw in cents

        Returns:
            The updated SavingsGoal or None if not found
        """
        goal = await self._savings_repo.withdraw_from_goal(goal_id, amount_cents)

        if goal and self._auto_commit:
            await self.session.commit()

        return goal

    async def list_savings_goals(self, include_completed: bool = False) -> Sequence[SavingsGoal]:
        """List savings goals.

        Args:
            include_completed: Whether to include completed goals

        Returns:
            List of SavingsGoals
        """
        return await self._savings_repo.get_all_goals(include_completed=include_completed)

    async def get_savings_goal(self, goal_id: int) -> Optional[SavingsGoal]:
        """Get a specific savings goal.

        Args:
            goal_id: The goal ID

        Returns:
            The SavingsGoal or None if not found
        """
        return await self._savings_repo.get_by_id(goal_id)

    async def abandon_goal(self, goal_id: int) -> Optional[SavingsGoal]:
        """Mark a goal as abandoned.

        Args:
            goal_id: The goal ID

        Returns:
            The updated SavingsGoal or None if not found
        """
        goal = await self._savings_repo.abandon_goal(goal_id)

        if goal and self._auto_commit:
            await self.session.commit()

        return goal

    # =========================================================================
    # Dashboard Stats
    # =========================================================================

    async def get_dashboard_stats(self) -> Dict:
        """Get dashboard statistics for display.

        Returns:
            Dictionary with balance, spending, and goals info
        """
        balance = await self.get_balance()
        spending_this_month = await self.get_spending_summary("month")
        active_goals = await self._savings_repo.get_active_goals()

        # Calculate total saved across all goals
        total_saved = sum(goal.current_amount for goal in active_goals)

        return {
            "balance_cents": balance,
            "spent_this_month_cents": spending_this_month["total_cents"],
            "active_goals_count": len(active_goals),
            "total_saved_cents": total_saved,
            "goals": [
                {
                    "id": g.id,
                    "name": g.name,
                    "emoji": g.emoji,
                    "current_cents": g.current_amount,
                    "target_cents": g.target_amount,
                    "progress_percent": round(
                        (g.current_amount / g.target_amount) * 100, 1
                    ) if g.target_amount > 0 else 0,
                }
                for g in active_goals
            ],
        }


__all__ = ["FinanceService"]
