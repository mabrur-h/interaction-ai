"""Achievements service for Wally Junior gamification."""

from typing import Any, Dict, List, Optional

from server.database.models import Achievement
from server.repositories.achievements import (
    AchievementRepository,
    ACHIEVEMENT_DEFINITIONS,
    get_all_achievement_types,
)


class AchievementsService:
    """Service for managing kid achievements and badges."""

    def __init__(
        self,
        achievement_repo: AchievementRepository,
        auto_commit: bool = True,
    ):
        """Initialize the achievements service.

        Args:
            achievement_repo: Repository for achievement operations
            auto_commit: Whether to auto-commit after operations
        """
        self.achievement_repo = achievement_repo
        self.auto_commit = auto_commit

    async def get_achievements(self) -> List[Dict[str, Any]]:
        """Get all earned achievements with details.

        Returns:
            List of achievement details with metadata
        """
        earned = await self.achievement_repo.get_earned_achievements()

        return [
            {
                "id": ach.id,
                "type": ach.achievement_type,
                "name": ACHIEVEMENT_DEFINITIONS.get(ach.achievement_type, {}).get(
                    "name", ach.achievement_type
                ),
                "description": ACHIEVEMENT_DEFINITIONS.get(ach.achievement_type, {}).get(
                    "description", ""
                ),
                "emoji": ACHIEVEMENT_DEFINITIONS.get(ach.achievement_type, {}).get(
                    "emoji", "🏅"
                ),
                "earned_at": ach.earned_at.isoformat(),
                "metadata": ach.metadata,
            }
            for ach in earned
        ]

    async def get_all_achievements(self) -> List[Dict[str, Any]]:
        """Get all possible achievements with earned status.

        Returns:
            List of all achievements with earned flag
        """
        earned = await self.achievement_repo.get_earned_achievements()
        earned_types = {ach.achievement_type: ach for ach in earned}

        all_achievements = []
        for ach_type, definition in ACHIEVEMENT_DEFINITIONS.items():
            earned_ach = earned_types.get(ach_type)
            all_achievements.append({
                "type": ach_type,
                "name": definition["name"],
                "description": definition["description"],
                "emoji": definition["emoji"],
                "earned": earned_ach is not None,
                "earned_at": earned_ach.earned_at.isoformat() if earned_ach else None,
            })

        return all_achievements

    async def get_achievement_progress(self) -> Dict[str, Any]:
        """Get achievement progress summary.

        Returns:
            Summary with counts and percentages
        """
        earned_count = await self.achievement_repo.get_achievement_count()
        total_count = len(ACHIEVEMENT_DEFINITIONS)

        return {
            "earned": earned_count,
            "total": total_count,
            "progress_percent": round((earned_count / total_count) * 100, 1)
            if total_count > 0
            else 0,
            "remaining": total_count - earned_count,
        }

    async def check_expense_achievements(self) -> List[Dict[str, Any]]:
        """Check for new expense-related achievements.

        Returns:
            List of newly earned achievement details
        """
        new_achievements = await self.achievement_repo.check_expense_achievements()
        return self._format_new_achievements(new_achievements)

    async def check_savings_achievements(self) -> List[Dict[str, Any]]:
        """Check for new savings-related achievements.

        Returns:
            List of newly earned achievement details
        """
        new_achievements = await self.achievement_repo.check_savings_achievements()
        return self._format_new_achievements(new_achievements)

    async def check_goal_completion(self, goal_name: str) -> List[Dict[str, Any]]:
        """Check for goal completion achievement.

        Args:
            goal_name: Name of the completed goal

        Returns:
            List of newly earned achievement details
        """
        new_achievements = await self.achievement_repo.check_goal_completion(goal_name)
        return self._format_new_achievements(new_achievements)

    async def check_all_achievements(self) -> List[Dict[str, Any]]:
        """Check for all possible new achievements.

        Returns:
            List of all newly earned achievement details
        """
        all_new = []
        all_new.extend(await self.check_expense_achievements())
        all_new.extend(await self.check_savings_achievements())
        return all_new

    def _format_new_achievements(
        self, achievements: List[Achievement]
    ) -> List[Dict[str, Any]]:
        """Format achievement objects into response dicts.

        Args:
            achievements: List of Achievement objects

        Returns:
            List of formatted achievement dicts
        """
        return [
            {
                "type": ach.achievement_type,
                "name": ACHIEVEMENT_DEFINITIONS.get(ach.achievement_type, {}).get(
                    "name", ach.achievement_type
                ),
                "description": ACHIEVEMENT_DEFINITIONS.get(ach.achievement_type, {}).get(
                    "description", ""
                ),
                "emoji": ACHIEVEMENT_DEFINITIONS.get(ach.achievement_type, {}).get(
                    "emoji", "🏅"
                ),
                "earned_at": ach.earned_at.isoformat(),
                "message": f"🎉 You earned the '{ACHIEVEMENT_DEFINITIONS.get(ach.achievement_type, {}).get('name', 'Achievement')}' badge!",
            }
            for ach in achievements
        ]
