"""Achievement tools for kids - badges and rewards for Wally Junior."""

from __future__ import annotations

from functools import partial
from typing import Any, Callable, Dict, List, Optional

from server.services.execution import get_execution_agent_logs

_SCHEMAS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "get_achievements",
            "description": "Get all the achievements and badges the kid has earned. Use this when they ask about their badges or achievements.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_all_badges",
            "description": "Get all possible badges with earned status. Use this to show the kid what badges they can work toward.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_new_achievements",
            "description": "Check if the kid has earned any new achievements. Call this after logging expenses or updating savings goals.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_achievement_progress",
            "description": "Get a summary of the kid's achievement progress - how many earned vs total.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
        },
    },
]

_LOG_STORE = get_execution_agent_logs()


def get_schemas() -> List[Dict[str, Any]]:
    """Return achievement tool schemas."""
    return _SCHEMAS


# =============================================================================
# Tool Implementation Functions
# =============================================================================


async def _get_achievements(
    *,
    agent_name: str,
    achievements_service: Any,
) -> Dict[str, Any]:
    """Get earned achievements."""
    try:
        achievements = await achievements_service.get_achievements()

        _LOG_STORE.record_action(
            agent_name,
            description=f"get_achievements succeeded | count={len(achievements)}",
        )

        if not achievements:
            return {
                "achievements": [],
                "count": 0,
                "message": "No badges earned yet! Keep tracking your spending and saving to earn badges!",
            }

        return {
            "achievements": achievements,
            "count": len(achievements),
            "message": f"You've earned {len(achievements)} badge{'s' if len(achievements) != 1 else ''}!",
        }
    except Exception as e:
        _LOG_STORE.record_action(
            agent_name,
            description=f"get_achievements failed | error={e}",
        )
        return {"error": str(e)}


async def _get_all_badges(
    *,
    agent_name: str,
    achievements_service: Any,
) -> Dict[str, Any]:
    """Get all possible badges with earned status."""
    try:
        all_badges = await achievements_service.get_all_achievements()
        earned = [b for b in all_badges if b["earned"]]
        locked = [b for b in all_badges if not b["earned"]]

        _LOG_STORE.record_action(
            agent_name,
            description=f"get_all_badges succeeded | earned={len(earned)} | locked={len(locked)}",
        )

        return {
            "earned_badges": earned,
            "locked_badges": locked,
            "earned_count": len(earned),
            "total_count": len(all_badges),
            "message": f"You've earned {len(earned)} of {len(all_badges)} badges! Keep going!",
        }
    except Exception as e:
        _LOG_STORE.record_action(
            agent_name,
            description=f"get_all_badges failed | error={e}",
        )
        return {"error": str(e)}


async def _check_new_achievements(
    *,
    agent_name: str,
    achievements_service: Any,
) -> Dict[str, Any]:
    """Check for newly earned achievements."""
    try:
        new_achievements = await achievements_service.check_all_achievements()

        _LOG_STORE.record_action(
            agent_name,
            description=f"check_new_achievements succeeded | new={len(new_achievements)}",
        )

        if not new_achievements:
            return {
                "new_achievements": [],
                "count": 0,
                "message": "No new badges this time. Keep going!",
            }

        # Format celebration message
        badge_names = [a["name"] for a in new_achievements]
        if len(badge_names) == 1:
            celebration = f"🎉 WOW! You just earned the '{badge_names[0]}' badge!"
        else:
            celebration = f"🎉 AMAZING! You earned {len(badge_names)} new badges: {', '.join(badge_names)}!"

        return {
            "new_achievements": new_achievements,
            "count": len(new_achievements),
            "celebration": celebration,
            "message": celebration,
        }
    except Exception as e:
        _LOG_STORE.record_action(
            agent_name,
            description=f"check_new_achievements failed | error={e}",
        )
        return {"error": str(e)}


async def _get_achievement_progress(
    *,
    agent_name: str,
    achievements_service: Any,
) -> Dict[str, Any]:
    """Get achievement progress summary."""
    try:
        progress = await achievements_service.get_achievement_progress()

        _LOG_STORE.record_action(
            agent_name,
            description=f"get_achievement_progress succeeded | {progress['earned']}/{progress['total']}",
        )

        return {
            **progress,
            "message": f"You've collected {progress['earned']} of {progress['total']} badges ({progress['progress_percent']}%)!",
        }
    except Exception as e:
        _LOG_STORE.record_action(
            agent_name,
            description=f"get_achievement_progress failed | error={e}",
        )
        return {"error": str(e)}


def build_registry(
    agent_name: str, achievements_service: Any = None
) -> Dict[str, Callable[..., Any]]:
    """Return achievement tool callables bound to a specific agent and service.

    Args:
        agent_name: Name of the execution agent
        achievements_service: AchievementsService instance

    Returns:
        Dictionary mapping tool names to callables
    """
    if achievements_service is None:
        return {}

    return {
        "get_achievements": partial(
            _get_achievements, agent_name=agent_name, achievements_service=achievements_service
        ),
        "get_all_badges": partial(
            _get_all_badges, agent_name=agent_name, achievements_service=achievements_service
        ),
        "check_new_achievements": partial(
            _check_new_achievements, agent_name=agent_name, achievements_service=achievements_service
        ),
        "get_achievement_progress": partial(
            _get_achievement_progress, agent_name=agent_name, achievements_service=achievements_service
        ),
    }


__all__ = [
    "build_registry",
    "get_schemas",
]
