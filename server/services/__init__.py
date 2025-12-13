"""Service layer components."""

from .calendar import (
    execute_calendar_tool,
    get_active_calendar_user_id,
)
from .conversation.chat_handler import handle_chat_request
from .execution import AgentRoster, ExecutionAgentLogStore, get_agent_roster, get_execution_agent_logs
from .gmail import (
    GmailSeenStore,
    ImportantEmailWatcher,
    classify_email_importance,
    execute_gmail_tool,
    get_active_gmail_user_id,
    get_important_email_watcher,
)
from .trigger_scheduler import get_trigger_scheduler
from .triggers import get_trigger_service
from .timezone_store import TimezoneStore, get_timezone_store


__all__ = [
    # Calendar
    "execute_calendar_tool",
    "get_active_calendar_user_id",
    # Conversation
    "handle_chat_request",
    # Execution
    "AgentRoster",
    "ExecutionAgentLogStore",
    "get_agent_roster",
    "get_execution_agent_logs",
    # Gmail
    "GmailSeenStore",
    "ImportantEmailWatcher",
    "classify_email_importance",
    "execute_gmail_tool",
    "get_active_gmail_user_id",
    "get_important_email_watcher",
    # Triggers
    "get_trigger_scheduler",
    "get_trigger_service",
    # Timezone (for background services without user context)
    "TimezoneStore",
    "get_timezone_store",
]
