"""Aggregate execution agent tool schemas and registries.

This module provides tools for adult users (Poke/OpenPoke).
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from . import utils


def get_tool_schemas() -> List[Dict[str, Any]]:
    """Return OpenAI/OpenRouter-compatible tool schemas.

    Returns:
        List of tool schemas for Poke finance tools
    """
    from .adult import finance

    schemas = [*utils.get_schemas()]
    schemas.extend(finance.get_schemas())

    return schemas


def get_tool_registry(
    agent_name: str,
    adult_finance_service: Optional[Any] = None,
    insights_service: Optional[Any] = None,
    user_id: Optional[str] = None,
    db_session: Optional[Any] = None,
) -> Dict[str, Callable[..., Any]]:
    """Return Python callables for executing tools by name.

    Args:
        agent_name: Name of the execution agent
        adult_finance_service: AdultFinanceService instance (required for finance tools)
        insights_service: InsightsService instance (optional, for insights)
        user_id: User ID for reminder operations (optional)
        db_session: Database session for reminder operations (optional)

    Returns:
        Dictionary mapping tool names to callables
    """
    from .adult import finance

    registry: Dict[str, Callable[..., Any]] = {}

    # Utility tools
    registry.update(utils.build_registry(agent_name))

    # Finance tools
    if adult_finance_service is not None:
        registry.update(
            finance.build_registry(
                agent_name,
                adult_finance_service,
                insights_service=insights_service,
                user_id=user_id,
                db_session=db_session,
            )
        )

    return registry


__all__ = [
    "get_tool_registry",
    "get_tool_schemas",
]
