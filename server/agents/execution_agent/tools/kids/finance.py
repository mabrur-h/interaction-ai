"""Finance tools for kids - expense tracking and savings goals for Wally Junior."""

from __future__ import annotations

from functools import partial
from typing import Any, Callable, Dict, List, Optional

from server.services.execution import get_execution_agent_logs

_SCHEMAS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "log_expense",
            "description": "Log an expense for the kid. Call this when they tell you about something they bought or spent money on.",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {
                        "type": "number",
                        "description": "Amount spent (e.g., 5000 for 5000 so'm)",
                    },
                    "category": {
                        "type": "string",
                        "enum": ["food", "toys", "games", "clothes", "books", "entertainment", "school", "other"],
                        "description": "What type of expense this is",
                    },
                    "description": {
                        "type": "string",
                        "description": "What was bought (e.g., 'candy', 'movie ticket', 'new pencils')",
                    },
                },
                "required": ["amount", "category"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_balance",
            "description": "Get the kid's current balance (their allowance minus what they've spent).",
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
            "name": "set_savings_goal",
            "description": "Create a new savings goal (piggy bank) for the kid. Use this when they want to save for something.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name of what they're saving for (e.g., 'New Bike', 'PlayStation Game', 'Headphones')",
                    },
                    "target_amount": {
                        "type": "number",
                        "description": "How much money they need (e.g., 500000 for 500,000 so'm)",
                    },
                    "emoji": {
                        "type": "string",
                        "description": "Optional emoji to represent the goal (e.g., '🎮', '🚲', '🎧')",
                    },
                },
                "required": ["name", "target_amount"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_to_savings",
            "description": "Add money to one of the kid's savings goals.",
            "parameters": {
                "type": "object",
                "properties": {
                    "goal_id": {
                        "type": "integer",
                        "description": "ID of the savings goal to add to",
                    },
                    "amount": {
                        "type": "number",
                        "description": "Amount to add (e.g., 10000 for 10,000 so'm)",
                    },
                },
                "required": ["goal_id", "amount"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_spending_summary",
            "description": "Get a summary of the kid's spending over a time period.",
            "parameters": {
                "type": "object",
                "properties": {
                    "period": {
                        "type": "string",
                        "enum": ["today", "week", "month", "all"],
                        "description": "Time period for the summary",
                    },
                },
                "required": ["period"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_savings_goals",
            "description": "List all of the kid's active savings goals (piggy banks).",
            "parameters": {
                "type": "object",
                "properties": {
                    "include_completed": {
                        "type": "boolean",
                        "description": "Whether to include completed goals (default: false)",
                    },
                },
                "required": [],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_dashboard",
            "description": "Get the kid's finance dashboard with balance, spending, and savings info.",
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
    """Return finance tool schemas."""
    return _SCHEMAS


# =============================================================================
# Tool Implementation Functions
# These are called with user context injected at runtime
# =============================================================================


async def _log_expense(
    *,
    agent_name: str,
    finance_service: Any,
    amount: float,
    category: str,
    description: Optional[str] = None,
) -> Dict[str, Any]:
    """Log an expense."""
    try:
        # Store amount as-is (input is in so'm)
        amount_cents = int(amount)

        expense = await finance_service.log_expense(
            amount_cents=amount_cents,
            category=category,
            description=description,
        )

        _LOG_STORE.record_action(
            agent_name,
            description=f"log_expense succeeded | amount={amount_cents} | category={category}",
        )

        return {
            "success": True,
            "expense_id": expense.id,
            "amount": amount_cents,
            "category": category,
            "description": description,
            "message": f"Logged {amount_cents:,} so'm for {category}" + (f" ({description})" if description else ""),
        }
    except Exception as e:
        _LOG_STORE.record_action(
            agent_name,
            description=f"log_expense failed | error={e}",
        )
        return {"error": str(e)}


async def _get_balance(
    *,
    agent_name: str,
    finance_service: Any,
) -> Dict[str, Any]:
    """Get current balance."""
    try:
        balance = await finance_service.get_balance()

        _LOG_STORE.record_action(
            agent_name,
            description=f"get_balance succeeded | balance={balance}",
        )

        return {
            "balance": balance,
            "formatted": f"{balance:,} so'm",
        }
    except Exception as e:
        _LOG_STORE.record_action(
            agent_name,
            description=f"get_balance failed | error={e}",
        )
        return {"error": str(e)}


async def _set_savings_goal(
    *,
    agent_name: str,
    finance_service: Any,
    name: str,
    target_amount: float,
    emoji: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a new savings goal."""
    try:
        # Store amount as-is (input is in so'm)
        target_cents = int(target_amount)

        goal = await finance_service.create_savings_goal(
            name=name,
            target_amount_cents=target_cents,
            emoji=emoji,
        )

        _LOG_STORE.record_action(
            agent_name,
            description=f"set_savings_goal succeeded | goal_id={goal.id} | name={name}",
        )

        return {
            "success": True,
            "goal_id": goal.id,
            "name": name,
            "target": target_cents,
            "emoji": emoji,
            "message": f"Created savings goal '{name}' for {target_cents:,} so'm!" + (f" {emoji}" if emoji else ""),
        }
    except Exception as e:
        _LOG_STORE.record_action(
            agent_name,
            description=f"set_savings_goal failed | error={e}",
        )
        return {"error": str(e)}


async def _add_to_savings(
    *,
    agent_name: str,
    finance_service: Any,
    goal_id: int,
    amount: float,
) -> Dict[str, Any]:
    """Add money to a savings goal."""
    try:
        # Store amount as-is (input is in so'm)
        amount_cents = int(amount)

        goal = await finance_service.add_to_savings(goal_id, amount_cents)

        if goal is None:
            return {"error": f"Goal {goal_id} not found"}

        progress = (goal.current_amount / goal.target_amount) * 100 if goal.target_amount > 0 else 0

        _LOG_STORE.record_action(
            agent_name,
            description=f"add_to_savings succeeded | goal_id={goal_id} | added={amount_cents} | progress={progress:.1f}%",
        )

        return {
            "success": True,
            "goal_id": goal.id,
            "name": goal.name,
            "current": goal.current_amount,
            "target": goal.target_amount,
            "progress_percent": round(progress, 1),
            "completed": goal.status == "completed",
            "message": f"Added {amount_cents:,} so'm to '{goal.name}'! Now at {progress:.0f}%",
        }
    except Exception as e:
        _LOG_STORE.record_action(
            agent_name,
            description=f"add_to_savings failed | error={e}",
        )
        return {"error": str(e)}


async def _get_spending_summary(
    *,
    agent_name: str,
    finance_service: Any,
    period: str,
) -> Dict[str, Any]:
    """Get spending summary."""
    try:
        summary = await finance_service.get_spending_summary(period)

        _LOG_STORE.record_action(
            agent_name,
            description=f"get_spending_summary succeeded | period={period} | total={summary['total_cents']}",
        )

        # Format for kid-friendly display
        formatted_categories = {
            k: f"{v:,} so'm" for k, v in summary["by_category"].items()
        }

        return {
            "period": period,
            "total": summary["total_cents"],
            "total_formatted": f"{summary['total_cents']:,} so'm",
            "by_category": summary["by_category"],
            "by_category_formatted": formatted_categories,
            "expense_count": summary["count"],
        }
    except Exception as e:
        _LOG_STORE.record_action(
            agent_name,
            description=f"get_spending_summary failed | error={e}",
        )
        return {"error": str(e)}


async def _list_savings_goals(
    *,
    agent_name: str,
    finance_service: Any,
    include_completed: bool = False,
) -> Dict[str, Any]:
    """List savings goals."""
    try:
        goals = await finance_service.list_savings_goals(include_completed=include_completed)

        _LOG_STORE.record_action(
            agent_name,
            description=f"list_savings_goals succeeded | count={len(goals)}",
        )

        return {
            "goals": [
                {
                    "id": g.id,
                    "name": g.name,
                    "emoji": g.emoji,
                    "current": g.current_amount,
                    "current_formatted": f"{g.current_amount:,} so'm",
                    "target": g.target_amount,
                    "target_formatted": f"{g.target_amount:,} so'm",
                    "progress_percent": round((g.current_amount / g.target_amount) * 100, 1) if g.target_amount > 0 else 0,
                    "status": g.status,
                }
                for g in goals
            ],
            "count": len(goals),
        }
    except Exception as e:
        _LOG_STORE.record_action(
            agent_name,
            description=f"list_savings_goals failed | error={e}",
        )
        return {"error": str(e)}


async def _get_dashboard(
    *,
    agent_name: str,
    finance_service: Any,
) -> Dict[str, Any]:
    """Get dashboard stats."""
    try:
        stats = await finance_service.get_dashboard_stats()

        _LOG_STORE.record_action(
            agent_name,
            description="get_dashboard succeeded",
        )

        return {
            "balance": stats["balance_cents"],
            "balance_formatted": f"{stats['balance_cents']:,} so'm",
            "spent_this_month": stats["spent_this_month_cents"],
            "spent_this_month_formatted": f"{stats['spent_this_month_cents']:,} so'm",
            "active_goals": stats["active_goals_count"],
            "total_saved": stats["total_saved_cents"],
            "total_saved_formatted": f"{stats['total_saved_cents']:,} so'm",
            "goals": stats["goals"],
        }
    except Exception as e:
        _LOG_STORE.record_action(
            agent_name,
            description=f"get_dashboard failed | error={e}",
        )
        return {"error": str(e)}


def build_registry(agent_name: str, finance_service: Any = None) -> Dict[str, Callable[..., Any]]:
    """Return finance tool callables bound to a specific agent and finance service.

    Note: finance_service must be passed when building registry for child users.
    """
    if finance_service is None:
        return {}

    return {
        "log_expense": partial(_log_expense, agent_name=agent_name, finance_service=finance_service),
        "get_balance": partial(_get_balance, agent_name=agent_name, finance_service=finance_service),
        "set_savings_goal": partial(_set_savings_goal, agent_name=agent_name, finance_service=finance_service),
        "add_to_savings": partial(_add_to_savings, agent_name=agent_name, finance_service=finance_service),
        "get_spending_summary": partial(_get_spending_summary, agent_name=agent_name, finance_service=finance_service),
        "list_savings_goals": partial(_list_savings_goals, agent_name=agent_name, finance_service=finance_service),
        "get_dashboard": partial(_get_dashboard, agent_name=agent_name, finance_service=finance_service),
    }


__all__ = [
    "build_registry",
    "get_schemas",
]
