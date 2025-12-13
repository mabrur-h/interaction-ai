"""Utility tools for execution agents that don't require external services."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from zoneinfo import ZoneInfo

from server.services.timezone_store import get_timezone_store


_SCHEMAS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "get_current_datetime",
            "description": "Get the current date and time. Use this for scheduling reminders or any time-based operations. Does NOT require Google Calendar to be connected.",
            "parameters": {
                "type": "object",
                "properties": {
                    "timezone": {
                        "type": "string",
                        "description": "Timezone to get current time in (e.g., 'UTC', 'America/New_York'). If not specified, uses the user's configured timezone.",
                    },
                },
                "additionalProperties": False,
            },
        },
    },
]


def get_schemas() -> List[Dict[str, Any]]:
    """Return utility tool schemas."""
    return _SCHEMAS


def get_current_datetime(
    timezone: Optional[str] = None,
) -> Dict[str, Any]:
    """Get the current date and time with timezone information.

    This is a standalone utility that doesn't require Google Calendar.
    """
    # Get timezone from parameter, user settings, or default to UTC
    tz_name = timezone
    if not tz_name:
        tz_store = get_timezone_store()
        tz_name = tz_store.get_timezone() or "UTC"

    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        # Fallback to UTC if timezone is invalid
        tz = ZoneInfo("UTC")
        tz_name = "UTC"

    now = datetime.now(tz)

    return {
        "current_datetime": now.isoformat(),
        "timezone": tz_name,
        "year": now.year,
        "month": now.month,
        "day": now.day,
        "hour": now.hour,
        "minute": now.minute,
        "second": now.second,
        "weekday": now.strftime("%A"),
        "date_formatted": now.strftime("%Y-%m-%d"),
        "time_formatted": now.strftime("%H:%M:%S"),
        "datetime_formatted": now.strftime("%Y-%m-%d %H:%M:%S %Z"),
    }


def build_registry(agent_name: str) -> Dict[str, Callable[..., Any]]:  # noqa: ARG001
    """Return utility tool callables."""
    return {
        "get_current_datetime": get_current_datetime,
    }


__all__ = [
    "build_registry",
    "get_schemas",
    "get_current_datetime",
]
