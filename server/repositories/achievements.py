"""Achievement repository for Wally Junior gamification."""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Sequence

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from server.database.models import Achievement, Expense, SavingsGoal
from server.repositories.base import UserScopedRepository


# Achievement type definitions
ACHIEVEMENT_DEFINITIONS = {
    "first_expense": {
        "name": "First Purchase",
        "description": "Logged your first expense",
        "emoji": "🛒",
    },
    "first_goal": {
        "name": "Dream Starter",
        "description": "Created your first savings goal",
        "emoji": "🌟",
    },
    "goal_complete": {
        "name": "Goal Crusher",
        "description": "Completed a savings goal",
        "emoji": "🏆",
    },
    "week_streak": {
        "name": "Super Saver",
        "description": "Logged expenses 7 days in a row",
        "emoji": "🔥",
    },
    "budget_under": {
        "name": "Budget Master",
        "description": "Spent less than your weekly limit",
        "emoji": "💪",
    },
    "savings_10k": {
        "name": "Piggy Bank Pro",
        "description": "Saved 10,000 so'm total",
        "emoji": "🐷",
    },
    "categories_3": {
        "name": "Smart Spender",
        "description": "Used 3 or more expense categories",
        "emoji": "🧠",
    },
    "savings_50k": {
        "name": "Money Master",
        "description": "Saved 50,000 so'm total",
        "emoji": "💰",
    },
    "goals_3": {
        "name": "Big Dreamer",
        "description": "Created 3 savings goals",
        "emoji": "✨",
    },
}


class AchievementRepository(UserScopedRepository[Achievement]):
    """Repository for Achievement operations (user-scoped)."""

    model = Achievement

    async def get_earned_achievements(self) -> Sequence[Achievement]:
        """Get all achievements earned by the user.

        Returns:
            List of Achievement objects
        """
        query = (
            select(Achievement)
            .where(Achievement.user_id == self.user_id)
            .order_by(Achievement.earned_at.desc())
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def has_achievement(self, achievement_type: str) -> bool:
        """Check if user has a specific achievement.

        Args:
            achievement_type: Type of achievement to check

        Returns:
            True if user has the achievement
        """
        query = select(Achievement.id).where(
            and_(
                Achievement.user_id == self.user_id,
                Achievement.achievement_type == achievement_type,
            )
        )
        result = await self.session.execute(query)
        return result.scalar() is not None

    async def award_achievement(
        self, achievement_type: str, extra_data: Optional[Dict] = None
    ) -> Optional[Achievement]:
        """Award an achievement to the user if not already earned.

        Args:
            achievement_type: Type of achievement to award
            extra_data: Optional additional data about the achievement

        Returns:
            The Achievement if newly awarded, None if already had it
        """
        if await self.has_achievement(achievement_type):
            return None

        return await self.create(
            achievement_type=achievement_type,
            extra_data=extra_data or {},
        )

    async def get_achievement_count(self) -> int:
        """Get the total number of achievements earned.

        Returns:
            Number of achievements
        """
        query = select(func.count(Achievement.id)).where(
            Achievement.user_id == self.user_id
        )
        result = await self.session.execute(query)
        return result.scalar() or 0

    # ==========================================================================
    # Achievement checking methods
    # ==========================================================================

    async def check_expense_achievements(self) -> List[Achievement]:
        """Check and award expense-related achievements.

        Returns:
            List of newly awarded achievements
        """
        new_achievements = []

        # First expense achievement
        if not await self.has_achievement("first_expense"):
            expense_count = await self._get_expense_count()
            if expense_count >= 1:
                ach = await self.award_achievement("first_expense")
                if ach:
                    new_achievements.append(ach)

        # Categories used achievement
        if not await self.has_achievement("categories_3"):
            categories_used = await self._get_unique_categories_count()
            if categories_used >= 3:
                ach = await self.award_achievement(
                    "categories_3", {"categories_count": categories_used}
                )
                if ach:
                    new_achievements.append(ach)

        # Week streak achievement
        if not await self.has_achievement("week_streak"):
            streak = await self._get_expense_streak_days()
            if streak >= 7:
                ach = await self.award_achievement("week_streak", {"streak_days": streak})
                if ach:
                    new_achievements.append(ach)

        return new_achievements

    async def check_savings_achievements(self) -> List[Achievement]:
        """Check and award savings-related achievements.

        Returns:
            List of newly awarded achievements
        """
        new_achievements = []

        # First goal achievement
        if not await self.has_achievement("first_goal"):
            goal_count = await self._get_goal_count()
            if goal_count >= 1:
                ach = await self.award_achievement("first_goal")
                if ach:
                    new_achievements.append(ach)

        # Multiple goals achievement
        if not await self.has_achievement("goals_3"):
            goal_count = await self._get_goal_count()
            if goal_count >= 3:
                ach = await self.award_achievement("goals_3", {"goal_count": goal_count})
                if ach:
                    new_achievements.append(ach)

        # Total saved achievements
        total_saved = await self._get_total_saved()

        if not await self.has_achievement("savings_10k") and total_saved >= 10000:
            ach = await self.award_achievement("savings_10k", {"total_saved": total_saved})
            if ach:
                new_achievements.append(ach)

        if not await self.has_achievement("savings_50k") and total_saved >= 50000:
            ach = await self.award_achievement("savings_50k", {"total_saved": total_saved})
            if ach:
                new_achievements.append(ach)

        return new_achievements

    async def check_goal_completion(self, goal_name: str) -> List[Achievement]:
        """Check and award goal completion achievement.

        Args:
            goal_name: Name of the completed goal

        Returns:
            List of newly awarded achievements
        """
        new_achievements = []

        # Award goal completion (can be earned multiple times in metadata)
        ach = await self.award_achievement(
            "goal_complete", {"completed_goal": goal_name}
        )
        if ach:
            new_achievements.append(ach)

        return new_achievements

    # ==========================================================================
    # Helper methods for achievement checks
    # ==========================================================================

    async def _get_expense_count(self) -> int:
        """Get total expense count for user."""
        query = select(func.count(Expense.id)).where(Expense.user_id == self.user_id)
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def _get_unique_categories_count(self) -> int:
        """Get count of unique expense categories used."""
        query = select(func.count(func.distinct(Expense.category))).where(
            Expense.user_id == self.user_id
        )
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def _get_expense_streak_days(self) -> int:
        """Get the current expense logging streak in days."""
        # Get dates with expenses, ordered by most recent
        query = (
            select(func.date(Expense.expense_date).label("expense_day"))
            .where(Expense.user_id == self.user_id)
            .group_by(func.date(Expense.expense_date))
            .order_by(func.date(Expense.expense_date).desc())
        )
        result = await self.session.execute(query)
        dates = [row.expense_day for row in result.all()]

        if not dates:
            return 0

        # Count consecutive days starting from today
        streak = 0
        expected_date = datetime.now().date()

        for expense_date in dates:
            if expense_date == expected_date:
                streak += 1
                expected_date -= timedelta(days=1)
            elif expense_date < expected_date:
                break

        return streak

    async def _get_goal_count(self) -> int:
        """Get total savings goal count for user."""
        query = select(func.count(SavingsGoal.id)).where(
            SavingsGoal.user_id == self.user_id
        )
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def _get_total_saved(self) -> int:
        """Get total amount saved across all goals."""
        query = select(func.coalesce(func.sum(SavingsGoal.current_amount), 0)).where(
            SavingsGoal.user_id == self.user_id
        )
        result = await self.session.execute(query)
        return result.scalar() or 0


def get_achievement_definitions() -> Dict:
    """Get all achievement definitions."""
    return ACHIEVEMENT_DEFINITIONS


def get_all_achievement_types() -> List[str]:
    """Get list of all achievement types."""
    return list(ACHIEVEMENT_DEFINITIONS.keys())
