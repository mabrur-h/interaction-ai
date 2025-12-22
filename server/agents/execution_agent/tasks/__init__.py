"""Task registry for execution agents.

Note: Email search tasks have been removed as part of Wally Junior simplification.
This module is kept for potential future task implementations.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List


def get_task_schemas() -> List[Dict[str, Any]]:
    """Return tool schemas contributed by task modules."""
    return []


def get_task_registry(agent_name: str) -> Dict[str, Callable[..., Any]]:
    """Return executable task tools keyed by name."""
    return {}


__all__ = [
    "get_task_registry",
    "get_task_schemas",
]
