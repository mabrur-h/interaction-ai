"""Google Calendar tool schemas and actions for the execution agent."""

from __future__ import annotations

import json
from typing import Any, Callable, Dict, List, Optional

from server.services.execution import get_execution_agent_logs
from server.services.calendar import execute_calendar_tool, get_active_calendar_user_id

_CALENDAR_AGENT_NAME = "calendar-execution-agent"

_SCHEMAS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "calendar_create_event",
            "description": "Create a new event on Google Calendar. Use RFC3339 format for timestamps (e.g., 2025-12-15T14:00:00Z).",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "string",
                        "description": "Title/summary of the event.",
                    },
                    "start_datetime": {
                        "type": "string",
                        "description": "Start time in RFC3339 format (e.g., 2025-12-15T14:00:00Z or 2025-12-15T14:00:00+05:30).",
                    },
                    "end_datetime": {
                        "type": "string",
                        "description": "End time in RFC3339 format (e.g., 2025-12-15T15:00:00Z).",
                    },
                    "description": {
                        "type": "string",
                        "description": "Optional description or notes for the event.",
                    },
                    "location": {
                        "type": "string",
                        "description": "Optional location for the event.",
                    },
                    "attendees": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of attendee email addresses.",
                    },
                    "calendar_id": {
                        "type": "string",
                        "description": "Calendar ID to create the event in. Defaults to 'primary'.",
                    },
                    "timezone": {
                        "type": "string",
                        "description": "Timezone for the event (e.g., 'America/New_York'). Uses calendar default if not specified.",
                    },
                },
                "required": ["summary", "start_datetime", "end_datetime"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calendar_list_events",
            "description": "List events from Google Calendar within a time range.",
            "parameters": {
                "type": "object",
                "properties": {
                    "calendar_id": {
                        "type": "string",
                        "description": "Calendar ID to list events from. Defaults to 'primary'.",
                    },
                    "time_min": {
                        "type": "string",
                        "description": "Start of time range in RFC3339 format. Defaults to current time.",
                    },
                    "time_max": {
                        "type": "string",
                        "description": "End of time range in RFC3339 format.",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of events to return. Defaults to 10.",
                    },
                    "query": {
                        "type": "string",
                        "description": "Free text search query to filter events.",
                    },
                    "order_by": {
                        "type": "string",
                        "description": "Order of events. Use 'startTime' or 'updated'.",
                    },
                },
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calendar_find_event",
            "description": "Find events in Google Calendar using a text query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Text query to search for in event titles, descriptions, etc.",
                    },
                    "calendar_id": {
                        "type": "string",
                        "description": "Calendar ID to search in. Defaults to 'primary'.",
                    },
                    "time_min": {
                        "type": "string",
                        "description": "Start of time range in RFC3339 format.",
                    },
                    "time_max": {
                        "type": "string",
                        "description": "End of time range in RFC3339 format.",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of events to return.",
                    },
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calendar_delete_event",
            "description": "Delete an event from Google Calendar.",
            "parameters": {
                "type": "object",
                "properties": {
                    "event_id": {
                        "type": "string",
                        "description": "ID of the event to delete.",
                    },
                    "calendar_id": {
                        "type": "string",
                        "description": "Calendar ID containing the event. Defaults to 'primary'.",
                    },
                },
                "required": ["event_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calendar_find_free_slots",
            "description": "Find available free time slots across calendars for scheduling.",
            "parameters": {
                "type": "object",
                "properties": {
                    "time_min": {
                        "type": "string",
                        "description": "Start of time range in RFC3339 format.",
                    },
                    "time_max": {
                        "type": "string",
                        "description": "End of time range in RFC3339 format.",
                    },
                    "timezone": {
                        "type": "string",
                        "description": "Timezone for the query (e.g., 'UTC', 'America/New_York').",
                    },
                    "calendars": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of calendar IDs to check. Defaults to ['primary'].",
                    },
                },
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calendar_get_current_datetime",
            "description": "Get the current date and time with timezone information. Useful for scheduling relative to now.",
            "parameters": {
                "type": "object",
                "properties": {
                    "timezone": {
                        "type": "string",
                        "description": "Timezone to get current time in (e.g., 'UTC', 'America/New_York').",
                    },
                },
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calendar_list_calendars",
            "description": "List all calendars available to the user.",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calendar_get_calendar",
            "description": "Get details about a specific calendar.",
            "parameters": {
                "type": "object",
                "properties": {
                    "calendar_id": {
                        "type": "string",
                        "description": "ID of the calendar to retrieve. Defaults to 'primary'.",
                    },
                },
                "additionalProperties": False,
            },
        },
    },
]

_LOG_STORE = get_execution_agent_logs()


def get_schemas() -> List[Dict[str, Any]]:
    """Return Google Calendar tool schemas."""
    return _SCHEMAS


def _execute(tool_name: str, composio_user_id: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a calendar tool and record the action for the execution agent journal."""
    payload = {k: v for k, v in arguments.items() if v is not None}
    payload_str = json.dumps(payload, ensure_ascii=False, sort_keys=True) if payload else "{}"
    try:
        result = execute_calendar_tool(tool_name, composio_user_id, arguments=payload)
    except Exception as exc:
        _LOG_STORE.record_action(
            _CALENDAR_AGENT_NAME,
            description=f"{tool_name} failed | args={payload_str} | error={exc}",
        )
        raise

    _LOG_STORE.record_action(
        _CALENDAR_AGENT_NAME,
        description=f"{tool_name} succeeded | args={payload_str}",
    )
    return result


def calendar_create_event(
    summary: str,
    start_datetime: str,
    end_datetime: str,
    description: Optional[str] = None,
    location: Optional[str] = None,
    attendees: Optional[List[str]] = None,
    calendar_id: Optional[str] = None,
    timezone: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a new event on Google Calendar."""
    arguments: Dict[str, Any] = {
        "summary": summary,
        "start_datetime": start_datetime,
        "end_datetime": end_datetime,
        "description": description,
        "location": location,
        "attendees": attendees,
        "calendar_id": calendar_id or "primary",
        "timezone": timezone,
    }
    composio_user_id = get_active_calendar_user_id()
    if not composio_user_id:
        return {"error": "Google Calendar not connected. Please connect Calendar in settings first."}
    return _execute("GOOGLECALENDAR_CREATE_EVENT", composio_user_id, arguments)


def calendar_list_events(
    calendar_id: Optional[str] = None,
    time_min: Optional[str] = None,
    time_max: Optional[str] = None,
    max_results: Optional[int] = None,
    query: Optional[str] = None,
    order_by: Optional[str] = None,
) -> Dict[str, Any]:
    """List events from Google Calendar within a time range."""
    arguments: Dict[str, Any] = {
        "calendar_id": calendar_id or "primary",
        "timeMin": time_min,
        "timeMax": time_max,
        "max_results": max_results or 10,
        "query": query,
        "order_by": order_by,
    }
    composio_user_id = get_active_calendar_user_id()
    if not composio_user_id:
        return {"error": "Google Calendar not connected. Please connect Calendar in settings first."}
    return _execute("GOOGLECALENDAR_EVENTS_LIST", composio_user_id, arguments)


def calendar_find_event(
    query: str,
    calendar_id: Optional[str] = None,
    time_min: Optional[str] = None,
    time_max: Optional[str] = None,
    max_results: Optional[int] = None,
) -> Dict[str, Any]:
    """Find events in Google Calendar using a text query."""
    arguments: Dict[str, Any] = {
        "query": query,
        "calendar_id": calendar_id or "primary",
        "timeMin": time_min,
        "timeMax": time_max,
        "max_results": max_results,
    }
    composio_user_id = get_active_calendar_user_id()
    if not composio_user_id:
        return {"error": "Google Calendar not connected. Please connect Calendar in settings first."}
    return _execute("GOOGLECALENDAR_FIND_EVENT", composio_user_id, arguments)


def calendar_delete_event(
    event_id: str,
    calendar_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Delete an event from Google Calendar."""
    arguments: Dict[str, Any] = {
        "event_id": event_id,
        "calendar_id": calendar_id or "primary",
    }
    composio_user_id = get_active_calendar_user_id()
    if not composio_user_id:
        return {"error": "Google Calendar not connected. Please connect Calendar in settings first."}
    return _execute("GOOGLECALENDAR_DELETE_EVENT", composio_user_id, arguments)


def calendar_find_free_slots(
    time_min: Optional[str] = None,
    time_max: Optional[str] = None,
    timezone: Optional[str] = None,
    calendars: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Find available free time slots across calendars."""
    arguments: Dict[str, Any] = {
        "time_min": time_min,
        "time_max": time_max,
        "timezone": timezone or "UTC",
        "items": calendars or ["primary"],
    }
    composio_user_id = get_active_calendar_user_id()
    if not composio_user_id:
        return {"error": "Google Calendar not connected. Please connect Calendar in settings first."}
    return _execute("GOOGLECALENDAR_FIND_FREE_SLOTS", composio_user_id, arguments)


def calendar_get_current_datetime(
    timezone: Optional[str] = None,
) -> Dict[str, Any]:
    """Get the current date and time with timezone information."""
    arguments: Dict[str, Any] = {
        "timezone": timezone,
    }
    composio_user_id = get_active_calendar_user_id()
    if not composio_user_id:
        return {"error": "Google Calendar not connected. Please connect Calendar in settings first."}
    return _execute("GOOGLECALENDAR_GET_CURRENT_DATE_TIME", composio_user_id, arguments)


def calendar_list_calendars() -> Dict[str, Any]:
    """List all calendars available to the user."""
    composio_user_id = get_active_calendar_user_id()
    if not composio_user_id:
        return {"error": "Google Calendar not connected. Please connect Calendar in settings first."}
    return _execute("GOOGLECALENDAR_LIST_CALENDARS", composio_user_id, {})


def calendar_get_calendar(
    calendar_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Get details about a specific calendar."""
    arguments: Dict[str, Any] = {
        "calendar_id": calendar_id or "primary",
    }
    composio_user_id = get_active_calendar_user_id()
    if not composio_user_id:
        return {"error": "Google Calendar not connected. Please connect Calendar in settings first."}
    return _execute("GOOGLECALENDAR_GET_CALENDAR", composio_user_id, arguments)


def build_registry(agent_name: str) -> Dict[str, Callable[..., Any]]:  # noqa: ARG001
    """Return Google Calendar tool callables."""
    return {
        "calendar_create_event": calendar_create_event,
        "calendar_list_events": calendar_list_events,
        "calendar_find_event": calendar_find_event,
        "calendar_delete_event": calendar_delete_event,
        "calendar_find_free_slots": calendar_find_free_slots,
        "calendar_get_current_datetime": calendar_get_current_datetime,
        "calendar_list_calendars": calendar_list_calendars,
        "calendar_get_calendar": calendar_get_calendar,
    }


__all__ = [
    "build_registry",
    "get_schemas",
    "calendar_create_event",
    "calendar_list_events",
    "calendar_find_event",
    "calendar_delete_event",
    "calendar_find_free_slots",
    "calendar_get_current_datetime",
    "calendar_list_calendars",
    "calendar_get_calendar",
]
