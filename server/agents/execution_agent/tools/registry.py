"""Aggregate execution agent tool schemas and registries.

This module routes tools based on user_type:
- 'child': Kids get finance + achievements tools (Wally Junior)
- 'adult': Adults get finance tools (Poke/OpenPoke)

Both user types get shared utility tools.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from . import utils


def get_tool_schemas(user_type: str = "adult") -> List[Dict[str, Any]]:
    """Return OpenAI/OpenRouter-compatible tool schemas.

    Args:
        user_type: 'adult' or 'child' - determines which tools are available

    Returns:
        List of tool schemas appropriate for the user type
    """
    # Utility tools are available for all users
    schemas = [*utils.get_schemas()]

    if user_type == "child":
        # Kids get Wally finance and achievements tools
        from .kids import finance, achievements
        schemas.extend(finance.get_schemas())
        schemas.extend(achievements.get_schemas())
    else:
        # Adults get Poke finance tools
        from .adult import finance
        schemas.extend(finance.get_schemas())

    return schemas


def get_tool_registry(
    agent_name: str,
    user_type: str = "adult",
    finance_service: Optional[Any] = None,
    achievements_service: Optional[Any] = None,
    adult_finance_service: Optional[Any] = None,
    insights_service: Optional[Any] = None,
) -> Dict[str, Callable[..., Any]]:
    """Return Python callables for executing tools by name.

    Args:
        agent_name: Name of the execution agent
        user_type: 'adult' or 'child'
        finance_service: FinanceService instance (required for child finance tools)
        achievements_service: AchievementsService instance (required for child achievements)
        adult_finance_service: AdultFinanceService instance (required for adult finance tools)
        insights_service: InsightsService instance (optional, for adult insights)

    Returns:
        Dictionary mapping tool names to callables
    """
    registry: Dict[str, Callable[..., Any]] = {}

    # Utility tools for everyone
    registry.update(utils.build_registry(agent_name))

    if user_type == "child":
        # Kids get Wally finance and achievements tools
        from .kids import finance, achievements

        if finance_service is not None:
            registry.update(finance.build_registry(agent_name, finance_service))

        if achievements_service is not None:
            registry.update(achievements.build_registry(agent_name, achievements_service))
    else:
        # Adults get Poke finance tools (with optional insights)
        from .adult import finance

        if adult_finance_service is not None:
            registry.update(
                finance.build_registry(
                    agent_name,
                    adult_finance_service,
                    insights_service=insights_service,
                )
            )

    return registry


__all__ = [
    "get_tool_registry",
    "get_tool_schemas",
]
