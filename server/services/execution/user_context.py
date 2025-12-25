"""User context for execution agents.

This module provides a way to pass user context (user_id, adult_finance_service)
to execution agents without modifying the entire call chain.
"""

import uuid
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class UserContext:
    """Context for the current user's execution session."""
    user_id: uuid.UUID
    adult_finance_service: Optional[Any] = None  # AdultFinanceService for finance tools


# Context variable to store user context
_user_context: ContextVar[Optional[UserContext]] = ContextVar("user_context", default=None)


def set_user_context(context: UserContext) -> None:
    """Set the current user context for execution agents."""
    _user_context.set(context)


def get_user_context() -> Optional[UserContext]:
    """Get the current user context."""
    return _user_context.get()


def clear_user_context() -> None:
    """Clear the current user context."""
    _user_context.set(None)


__all__ = [
    "UserContext",
    "set_user_context",
    "get_user_context",
    "clear_user_context",
]
