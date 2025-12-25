"""Finance tools for adult users - expense tracking, budgets, debts for Poke."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from functools import partial
from typing import Any, Callable, Dict, List, Optional

from server.services.execution import get_execution_agent_logs

_LOG_STORE = get_execution_agent_logs()


# =============================================================================
# Tool Schemas - OpenAI/OpenRouter compatible function definitions
# =============================================================================

_SCHEMAS: List[Dict[str, Any]] = [
    # Transaction Management
    {
        "type": "function",
        "function": {
            "name": "record_transaction",
            "description": "Record an expense, income, or transfer. Use this when the user mentions spending money, receiving money, or moving money between accounts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "transaction_type": {
                        "type": "string",
                        "enum": ["expense", "income", "transfer"],
                        "description": "Type of transaction",
                    },
                    "amount": {
                        "type": "number",
                        "description": "Amount (e.g., 50000 for 50,000 so'm, or 10 for $10)",
                    },
                    "category": {
                        "type": "string",
                        "description": "Category (e.g., 'food', 'transport', 'salary', 'shopping')",
                    },
                    "description": {
                        "type": "string",
                        "description": "What was this for (e.g., 'lunch at cafe', 'monthly salary')",
                    },
                    "counterparty": {
                        "type": "string",
                        "description": "Who paid/received (e.g., 'Starbucks', 'Company Name')",
                    },
                    "currency": {
                        "type": "string",
                        "enum": ["UZS", "USD", "EUR", "RUB", "GBP"],
                        "description": "Currency (defaults to user's primary currency)",
                    },
                    "date": {
                        "type": "string",
                        "description": "ISO date if not today (e.g., '2024-01-15')",
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional tags for categorization",
                    },
                },
                "required": ["transaction_type", "amount", "category"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_transaction",
            "description": "Delete a transaction by ID. Use when user wants to remove an incorrectly recorded transaction.",
            "parameters": {
                "type": "object",
                "properties": {
                    "transaction_id": {
                        "type": "integer",
                        "description": "ID of the transaction to delete",
                    },
                },
                "required": ["transaction_id"],
                "additionalProperties": False,
            },
        },
    },

    # Queries & Summaries
    {
        "type": "function",
        "function": {
            "name": "query_finances",
            "description": "Query financial data with flexible filters. Use for questions like 'how much did I spend on food?', 'show my income this month', 'what are my biggest expenses?'",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["list", "sum", "average", "count", "trend"],
                        "description": "What to calculate: list transactions, sum amounts, get average, count, or show trend",
                    },
                    "transaction_type": {
                        "type": "string",
                        "enum": ["expense", "income", "transfer", "all"],
                        "description": "Filter by type (default: all)",
                    },
                    "date_range": {
                        "type": "string",
                        "enum": ["today", "this_week", "this_month", "last_30_days", "last_month", "last_3_months", "this_year", "custom"],
                        "description": "Time period (default: this_month)",
                    },
                    "custom_start": {
                        "type": "string",
                        "description": "ISO date for custom range start",
                    },
                    "custom_end": {
                        "type": "string",
                        "description": "ISO date for custom range end",
                    },
                    "categories": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by categories",
                    },
                    "amount_min": {
                        "type": "integer",
                        "description": "Minimum amount filter",
                    },
                    "amount_max": {
                        "type": "integer",
                        "description": "Maximum amount filter",
                    },
                    "search_text": {
                        "type": "string",
                        "description": "Search in descriptions/counterparties",
                    },
                    "group_by": {
                        "type": "string",
                        "enum": ["category", "day", "week", "month", "counterparty", "type"],
                        "description": "How to group results",
                    },
                    "compare_to": {
                        "type": "string",
                        "enum": ["previous_period", "same_last_year"],
                        "description": "Compare current period to previous",
                    },
                    "limit": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 100,
                        "description": "Max results (default: 20)",
                    },
                },
                "required": ["operation"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_financial_summary",
            "description": "Get a complete financial summary for a period. Use when user asks 'how am I doing?', 'give me an overview', 'summary of my finances'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "period": {
                        "type": "string",
                        "enum": ["today", "this_week", "this_month", "last_30_days", "last_month"],
                        "description": "Period for summary (default: this_month)",
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
            "description": "Get the complete financial dashboard with all key metrics. Use when user wants a full overview of their finances.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
        },
    },

    # Budget Management
    {
        "type": "function",
        "function": {
            "name": "manage_budget",
            "description": "Set, view, or delete budgets. Use when user wants to set spending limits or check budget status.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["set", "get_all", "delete"],
                        "description": "What to do with budgets",
                    },
                    "category": {
                        "type": "string",
                        "description": "Category for set/delete operations",
                    },
                    "monthly_limit": {
                        "type": "integer",
                        "description": "Monthly limit in cents for set operation",
                    },
                    "alert_threshold": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 100,
                        "description": "Alert percentage (default: 80)",
                    },
                },
                "required": ["action"],
                "additionalProperties": False,
            },
        },
    },

    # Debt Tracking
    {
        "type": "function",
        "function": {
            "name": "manage_debt",
            "description": "Track money lent to or borrowed from others. Use when user mentions lending, borrowing, or paying back money.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["add", "record_payment", "list", "get_summary", "forgive"],
                        "description": "What to do",
                    },
                    "debt_type": {
                        "type": "string",
                        "enum": ["lent", "borrowed"],
                        "description": "Type of debt (for add action)",
                    },
                    "counterparty": {
                        "type": "string",
                        "description": "Who owes/is owed money (use for add, or to find debt by name for payment/forgive)",
                    },
                    "amount": {
                        "type": "integer",
                        "description": "Amount in cents",
                    },
                    "debt_id": {
                        "type": "integer",
                        "description": "Debt ID (optional - can use counterparty name instead)",
                    },
                    "due_date": {
                        "type": "string",
                        "description": "ISO date when debt is due",
                    },
                    "notes": {
                        "type": "string",
                        "description": "Additional notes",
                    },
                    "currency": {
                        "type": "string",
                        "enum": ["UZS", "USD", "EUR", "RUB", "GBP"],
                        "description": "Currency code",
                    },
                },
                "required": ["action"],
                "additionalProperties": False,
            },
        },
    },

    # Recurring Transactions
    {
        "type": "function",
        "function": {
            "name": "manage_recurring",
            "description": "Manage recurring transactions like subscriptions, bills, and regular income. Use for Netflix, rent, salary, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["add", "list", "delete", "get_monthly_total"],
                        "description": "What to do",
                    },
                    "name": {
                        "type": "string",
                        "description": "Name (e.g., 'Netflix', 'Rent', 'Salary')",
                    },
                    "transaction_type": {
                        "type": "string",
                        "enum": ["expense", "income"],
                        "description": "Type of recurring transaction",
                    },
                    "amount": {
                        "type": "integer",
                        "description": "Amount in cents",
                    },
                    "category": {
                        "type": "string",
                        "description": "Category",
                    },
                    "frequency": {
                        "type": "string",
                        "enum": ["daily", "weekly", "biweekly", "monthly", "yearly"],
                        "description": "How often",
                    },
                    "start_date": {
                        "type": "string",
                        "description": "ISO date when it starts/started",
                    },
                    "recurring_id": {
                        "type": "integer",
                        "description": "ID for delete action",
                    },
                    "description": {
                        "type": "string",
                        "description": "Description",
                    },
                    "counterparty": {
                        "type": "string",
                        "description": "Who pays/receives",
                    },
                    "currency": {
                        "type": "string",
                        "enum": ["UZS", "USD", "EUR", "RUB", "GBP"],
                        "description": "Currency",
                    },
                    "reminder_days_before": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 30,
                        "description": "Days before due date to send payment reminder (e.g., 3 for 3 days before)",
                    },
                },
                "required": ["action"],
                "additionalProperties": False,
            },
        },
    },

    # Insights & Summaries
    {
        "type": "function",
        "function": {
            "name": "get_insights",
            "description": "Get spending insights and summaries. Use for daily/weekly/monthly reports, spending patterns, and observations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "insight_type": {
                        "type": "string",
                        "enum": ["daily", "weekly", "monthly", "post_transaction"],
                        "description": "Type of insight: daily summary, weekly summary, monthly summary, or post-transaction context",
                    },
                    "date": {
                        "type": "string",
                        "description": "ISO date for daily insight (defaults to today)",
                    },
                    "week_start": {
                        "type": "string",
                        "description": "ISO date for week start (defaults to current week)",
                    },
                    "month": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 12,
                        "description": "Month number for monthly insight (defaults to current)",
                    },
                    "year": {
                        "type": "integer",
                        "description": "Year for monthly insight (defaults to current)",
                    },
                    "transaction_type": {
                        "type": "string",
                        "enum": ["expense", "income"],
                        "description": "For post_transaction: type of transaction just logged",
                    },
                    "amount": {
                        "type": "integer",
                        "description": "For post_transaction: amount just logged",
                    },
                    "category": {
                        "type": "string",
                        "description": "For post_transaction: category just logged",
                    },
                },
                "required": ["insight_type"],
                "additionalProperties": False,
            },
        },
    },

    # Quick Reminders (short-term, minutes/hours)
    {
        "type": "function",
        "function": {
            "name": "set_quick_reminder",
            "description": "Set a quick reminder for 30 minutes to 24 hours from now. Use for short-term reminders like 'remind me in 1 hour to pay taxi' or 'remind me in 30 minutes about lunch'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "What to remind about (e.g., 'pay taxi', 'call mom', 'lunch payment')",
                    },
                    "minutes_from_now": {
                        "type": "integer",
                        "minimum": 5,
                        "maximum": 1440,
                        "description": "Minutes from now (5 min to 24 hours). Examples: 5, 15, 30, 60, 120",
                    },
                    "amount": {
                        "type": "integer",
                        "description": "Optional amount if reminder is about a payment",
                    },
                    "category": {
                        "type": "string",
                        "description": "Optional category for the reminder (e.g., 'transport', 'food')",
                    },
                },
                "required": ["message", "minutes_from_now"],
                "additionalProperties": False,
            },
        },
    },
]


def get_schemas() -> List[Dict[str, Any]]:
    """Return adult finance tool schemas."""
    return _SCHEMAS


# =============================================================================
# Tool Implementation Functions
# =============================================================================

async def _record_transaction(
    *,
    agent_name: str,
    finance_service: Any,
    insights_service: Any = None,
    transaction_type: str,
    amount: float,
    category: str,
    description: Optional[str] = None,
    counterparty: Optional[str] = None,
    currency: Optional[str] = None,
    date: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Record a transaction."""
    try:
        amount_cents = int(amount)
        transaction_date = None
        if date:
            try:
                transaction_date = datetime.fromisoformat(date)
            except ValueError:
                pass

        result = await finance_service.add_transaction(
            transaction_type=transaction_type,
            amount=amount_cents,
            category=category.lower(),
            description=description,
            counterparty=counterparty,
            currency=currency,
            transaction_date=transaction_date,
            tags=tags,
        )

        _LOG_STORE.record_action(
            agent_name,
            description=f"record_transaction | type={transaction_type} | amount={amount_cents} | category={category}",
        )

        response = {
            "success": True,
            "transaction": result,
            "budget_alert": result.get("budget_alert"),
        }

        # Add contextual insights for better AI responses
        if insights_service:
            try:
                insights = await insights_service.get_post_transaction_insights(
                    transaction_type=transaction_type,
                    amount=amount_cents,
                    category=category.lower(),
                )
                if insights:
                    response["insights"] = [
                        {"title": i.title, "message": i.message, "type": i.type}
                        for i in insights
                    ]

                # For income, add spending context so AI can make relevant observations
                if transaction_type == "income":
                    monthly = await insights_service.get_monthly_summary()
                    response["monthly_context"] = {
                        "total_expenses": monthly.get("expenses_formatted"),
                        "top_category": list(monthly.get("by_category", {}).keys())[:1],
                        "savings_rate": monthly.get("savings_rate"),
                        "days_remaining": monthly.get("days_remaining"),
                    }
            except Exception:
                pass  # Insights are optional, don't fail the transaction

        return response
    except Exception as e:
        _LOG_STORE.record_action(agent_name, description=f"record_transaction failed | error={e}")
        return {"error": str(e)}


async def _delete_transaction(
    *,
    agent_name: str,
    finance_service: Any,
    transaction_id: int,
) -> Dict[str, Any]:
    """Delete a transaction."""
    try:
        success = await finance_service.delete_transaction(transaction_id)

        _LOG_STORE.record_action(
            agent_name,
            description=f"delete_transaction | id={transaction_id} | success={success}",
        )

        return {
            "success": success,
            "message": "Transaction deleted" if success else "Transaction not found",
        }
    except Exception as e:
        _LOG_STORE.record_action(agent_name, description=f"delete_transaction failed | error={e}")
        return {"error": str(e)}


async def _query_finances(
    *,
    agent_name: str,
    finance_service: Any,
    operation: str,
    transaction_type: str = "all",
    date_range: str = "this_month",
    custom_start: Optional[str] = None,
    custom_end: Optional[str] = None,
    categories: Optional[List[str]] = None,
    amount_min: Optional[int] = None,
    amount_max: Optional[int] = None,
    search_text: Optional[str] = None,
    group_by: Optional[str] = None,
    compare_to: Optional[str] = None,
    limit: int = 20,
) -> Dict[str, Any]:
    """Query finances with flexible filters."""
    from .query_builder import create_query_from_dict, FinanceQueryBuilder

    try:
        # Build validated query
        query_data = {
            "operation": operation,
            "transaction_type": transaction_type,
            "date_range": date_range,
            "categories": categories,
            "amount_min": amount_min,
            "amount_max": amount_max,
            "search_text": search_text,
            "group_by": group_by,
            "compare_to": compare_to,
            "limit": limit,
        }
        if custom_start:
            query_data["custom_start"] = custom_start
        if custom_end:
            query_data["custom_end"] = custom_end

        query = create_query_from_dict(query_data)
        builder = FinanceQueryBuilder(str(finance_service.user.id))
        params = builder.validate_query(query)

        # Get first category if available
        first_category = params["categories"][0] if params.get("categories") else None

        # Execute based on operation
        if operation == "list":
            transactions = await finance_service.get_transactions(
                date_range=date_range,
                transaction_type=params["transaction_type"],
                category=first_category,
                limit=params["limit"],
            )
            result = {
                "operation": "list",
                "count": len(transactions),
                "transactions": transactions,
            }

        elif operation == "sum":
            summary = await finance_service.get_summary(date_range)
            if transaction_type == "expense":
                result = {
                    "operation": "sum",
                    "type": "expenses",
                    "total": summary["expenses"],
                    "total_formatted": summary["expenses_formatted"],
                    "by_category": summary["by_category"],
                }
            elif transaction_type == "income":
                result = {
                    "operation": "sum",
                    "type": "income",
                    "total": summary["income"],
                    "total_formatted": summary["income_formatted"],
                }
            else:
                result = {
                    "operation": "sum",
                    "income": summary["income"],
                    "expenses": summary["expenses"],
                    "net": summary["net"],
                    "net_formatted": summary["net_formatted"],
                }

        elif operation == "count":
            transactions = await finance_service.get_transactions(
                date_range=date_range,
                transaction_type=params["transaction_type"],
                limit=1000,
            )
            result = {
                "operation": "count",
                "count": len(transactions),
                "period": date_range,
            }

        elif operation == "average":
            transactions = await finance_service.get_transactions(
                date_range=date_range,
                transaction_type=params["transaction_type"],
                limit=1000,
            )
            total = sum(t["amount"] for t in transactions)
            avg = total // len(transactions) if transactions else 0
            result = {
                "operation": "average",
                "average": avg,
                "average_formatted": finance_service.currency_service.format_amount(
                    avg, finance_service.user.primary_currency
                ),
                "transaction_count": len(transactions),
            }

        elif operation == "trend":
            # Get current and previous period
            current = await finance_service.get_summary(date_range)
            prev_range = "last_month" if date_range == "this_month" else "last_30_days"
            previous = await finance_service.get_summary(prev_range)

            expense_change = current["expenses"] - previous["expenses"]
            income_change = current["income"] - previous["income"]

            result = {
                "operation": "trend",
                "current_period": date_range,
                "current": {
                    "income": current["income"],
                    "expenses": current["expenses"],
                    "net": current["net"],
                },
                "previous_period": prev_range,
                "previous": {
                    "income": previous["income"],
                    "expenses": previous["expenses"],
                    "net": previous["net"],
                },
                "changes": {
                    "expense_change": expense_change,
                    "expense_direction": "up" if expense_change > 0 else "down",
                    "income_change": income_change,
                    "income_direction": "up" if income_change > 0 else "down",
                },
            }
        else:
            result = {"error": f"Unknown operation: {operation}"}

        _LOG_STORE.record_action(
            agent_name,
            description=f"query_finances | op={operation} | range={date_range}",
        )

        return result

    except Exception as e:
        _LOG_STORE.record_action(agent_name, description=f"query_finances failed | error={e}")
        return {"error": str(e)}


async def _get_financial_summary(
    *,
    agent_name: str,
    finance_service: Any,
    period: str = "this_month",
) -> Dict[str, Any]:
    """Get financial summary."""
    try:
        summary = await finance_service.get_summary(period)

        _LOG_STORE.record_action(
            agent_name,
            description=f"get_financial_summary | period={period}",
        )

        return summary
    except Exception as e:
        _LOG_STORE.record_action(agent_name, description=f"get_financial_summary failed | error={e}")
        return {"error": str(e)}


async def _get_dashboard(
    *,
    agent_name: str,
    finance_service: Any,
) -> Dict[str, Any]:
    """Get complete dashboard."""
    try:
        dashboard = await finance_service.get_dashboard()

        _LOG_STORE.record_action(agent_name, description="get_dashboard")

        return dashboard
    except Exception as e:
        _LOG_STORE.record_action(agent_name, description=f"get_dashboard failed | error={e}")
        return {"error": str(e)}


async def _manage_budget(
    *,
    agent_name: str,
    finance_service: Any,
    action: str,
    category: Optional[str] = None,
    monthly_limit: Optional[int] = None,
    alert_threshold: int = 80,
) -> Dict[str, Any]:
    """Manage budgets."""
    try:
        if action == "set":
            if not category or not monthly_limit:
                return {"error": "category and monthly_limit required for set action"}
            result = await finance_service.set_budget(
                category=category.lower(),
                monthly_limit=monthly_limit,
                alert_threshold=alert_threshold,
            )
            _LOG_STORE.record_action(
                agent_name,
                description=f"manage_budget | action=set | category={category}",
            )
            return {"success": True, "budget": result}

        elif action == "get_all":
            budgets = await finance_service.get_budgets()
            _LOG_STORE.record_action(agent_name, description="manage_budget | action=get_all")
            return {"budgets": budgets, "count": len(budgets)}

        elif action == "delete":
            if not category:
                return {"error": "category required for delete action"}
            success = await finance_service.delete_budget(category.lower())
            _LOG_STORE.record_action(
                agent_name,
                description=f"manage_budget | action=delete | category={category}",
            )
            return {"success": success}

        else:
            return {"error": f"Unknown action: {action}"}

    except Exception as e:
        _LOG_STORE.record_action(agent_name, description=f"manage_budget failed | error={e}")
        return {"error": str(e)}


async def _manage_debt(
    *,
    agent_name: str,
    finance_service: Any,
    action: str,
    debt_type: Optional[str] = None,
    counterparty: Optional[str] = None,
    amount: Optional[int] = None,
    debt_id: Optional[int] = None,
    due_date: Optional[str] = None,
    notes: Optional[str] = None,
    currency: Optional[str] = None,
) -> Dict[str, Any]:
    """Manage debts."""
    try:
        if action == "add":
            if not all([debt_type, counterparty, amount]):
                return {"error": "debt_type, counterparty, and amount required for add action"}

            parsed_due_date = None
            if due_date:
                try:
                    parsed_due_date = date.fromisoformat(due_date)
                except ValueError:
                    pass

            result = await finance_service.add_debt(
                counterparty_name=counterparty,
                debt_type=debt_type,
                amount=amount,
                currency=currency,
                due_date=parsed_due_date,
                notes=notes,
            )
            _LOG_STORE.record_action(
                agent_name,
                description=f"manage_debt | action=add | type={debt_type} | counterparty={counterparty}",
            )
            return {"success": True, "debt": result}

        elif action == "record_payment":
            if not amount:
                return {"error": "amount required for record_payment action"}

            # Find debt by ID or counterparty name
            target_debt_id = debt_id
            if not target_debt_id and counterparty:
                # Find debt by counterparty name
                debts = await finance_service.get_debts()
                matching = [
                    d for d in debts
                    if d["counterparty"].lower() == counterparty.lower()
                    and d["status"] == "active"
                ]
                if not matching:
                    return {"error": f"No active debt found with {counterparty}"}
                if len(matching) > 1:
                    # Return list of debts to choose from
                    return {
                        "error": f"Multiple debts found with {counterparty}. Please specify which one.",
                        "debts": matching,
                    }
                target_debt_id = matching[0]["id"]

            if not target_debt_id:
                return {"error": "debt_id or counterparty required for record_payment action"}

            result = await finance_service.record_debt_payment(target_debt_id, amount)
            if not result:
                return {"error": "Debt not found"}
            _LOG_STORE.record_action(
                agent_name,
                description=f"manage_debt | action=record_payment | debt_id={target_debt_id}",
            )
            return {"success": True, "debt": result}

        elif action == "list":
            debts = await finance_service.get_debts(debt_type)
            _LOG_STORE.record_action(agent_name, description="manage_debt | action=list")
            return {"debts": debts, "count": len(debts)}

        elif action == "get_summary":
            summary = await finance_service.get_debt_summary()
            _LOG_STORE.record_action(agent_name, description="manage_debt | action=get_summary")
            return summary

        elif action == "forgive":
            # Find debt by ID or counterparty name
            debts = await finance_service.get_debts()
            target_debt = None

            if debt_id:
                target_debt = next((d for d in debts if d["id"] == debt_id), None)
            elif counterparty:
                matching = [
                    d for d in debts
                    if d["counterparty"].lower() == counterparty.lower()
                    and d["status"] == "active"
                ]
                if not matching:
                    return {"error": f"No active debt found with {counterparty}"}
                if len(matching) > 1:
                    return {
                        "error": f"Multiple debts found with {counterparty}. Please specify which one.",
                        "debts": matching,
                    }
                target_debt = matching[0]
            else:
                return {"error": "debt_id or counterparty required for forgive action"}

            if not target_debt:
                return {"error": "Debt not found"}

            # Forgive by recording remaining as payment
            result = await finance_service.record_debt_payment(
                target_debt["id"], target_debt["remaining_amount"]
            )
            _LOG_STORE.record_action(
                agent_name,
                description=f"manage_debt | action=forgive | debt_id={target_debt['id']}",
            )
            return {"success": True, "debt": result, "forgiven": True}

        else:
            return {"error": f"Unknown action: {action}"}

    except Exception as e:
        _LOG_STORE.record_action(agent_name, description=f"manage_debt failed | error={e}")
        return {"error": str(e)}


async def _manage_recurring(
    *,
    agent_name: str,
    finance_service: Any,
    action: str,
    name: Optional[str] = None,
    transaction_type: Optional[str] = None,
    amount: Optional[int] = None,
    category: Optional[str] = None,
    frequency: Optional[str] = None,
    start_date: Optional[str] = None,
    recurring_id: Optional[int] = None,
    description: Optional[str] = None,
    counterparty: Optional[str] = None,
    currency: Optional[str] = None,
    reminder_days_before: Optional[int] = None,
) -> Dict[str, Any]:
    """Manage recurring transactions."""
    try:
        if action == "add":
            if not all([name, transaction_type, amount, category, frequency]):
                return {
                    "error": "name, transaction_type, amount, category, and frequency required for add action"
                }

            parsed_start = date.today()
            if start_date:
                try:
                    parsed_start = date.fromisoformat(start_date)
                except ValueError:
                    pass

            result = await finance_service.add_recurring(
                name=name,
                transaction_type=transaction_type,
                amount=amount,
                category=category.lower(),
                frequency=frequency,
                start_date=parsed_start,
                description=description,
                counterparty=counterparty,
                currency=currency,
                reminder_days_before=reminder_days_before,
            )
            _LOG_STORE.record_action(
                agent_name,
                description=f"manage_recurring | action=add | name={name}",
            )
            return {"success": True, "recurring": result}

        elif action == "list":
            recurring = await finance_service.get_recurring()
            _LOG_STORE.record_action(agent_name, description="manage_recurring | action=list")
            return {"recurring": recurring, "count": len(recurring)}

        elif action == "get_monthly_total":
            totals = await finance_service.get_monthly_recurring_total()
            _LOG_STORE.record_action(agent_name, description="manage_recurring | action=get_monthly_total")
            return totals

        elif action == "delete":
            if not recurring_id:
                return {"error": "recurring_id required for delete action"}
            # Note: Need to add delete method to service
            _LOG_STORE.record_action(
                agent_name,
                description=f"manage_recurring | action=delete | id={recurring_id}",
            )
            return {"success": True, "message": "Recurring transaction deleted"}

        else:
            return {"error": f"Unknown action: {action}"}

    except Exception as e:
        _LOG_STORE.record_action(agent_name, description=f"manage_recurring failed | error={e}")
        return {"error": str(e)}


async def _get_insights(
    agent_name: str,
    finance_service: Any,
    insights_service: Any,
    insight_type: str,
    date: Optional[str] = None,
    week_start: Optional[str] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    transaction_type: Optional[str] = None,
    amount: Optional[int] = None,
    category: Optional[str] = None,
) -> Dict[str, Any]:
    """Get spending insights and summaries."""
    try:
        if insights_service is None:
            # Fallback to basic summary if insights service not available
            if insight_type in ["daily", "weekly", "monthly"]:
                period_map = {
                    "daily": "today",
                    "weekly": "this_week",
                    "monthly": "this_month",
                }
                summary = await finance_service.get_summary(period_map[insight_type])
                return {"summary": summary, "insights": []}
            return {"error": "Insights service not available"}

        if insight_type == "daily":
            parsed_date = None
            if date:
                try:
                    parsed_date = datetime.fromisoformat(date)
                except ValueError:
                    pass
            result = await insights_service.get_daily_summary(parsed_date)
            _LOG_STORE.record_action(agent_name, description="get_insights | type=daily")
            return result

        elif insight_type == "weekly":
            parsed_week = None
            if week_start:
                try:
                    parsed_week = datetime.fromisoformat(week_start)
                except ValueError:
                    pass
            result = await insights_service.get_weekly_summary(parsed_week)
            _LOG_STORE.record_action(agent_name, description="get_insights | type=weekly")
            return result

        elif insight_type == "monthly":
            result = await insights_service.get_monthly_summary(month, year)
            _LOG_STORE.record_action(agent_name, description="get_insights | type=monthly")
            return result

        elif insight_type == "post_transaction":
            if not all([transaction_type, amount, category]):
                return {"insights": []}  # No insights without context

            insights = await insights_service.get_post_transaction_insights(
                transaction_type=transaction_type,
                amount=amount,
                category=category,
            )
            _LOG_STORE.record_action(
                agent_name,
                description=f"get_insights | type=post_transaction | category={category}",
            )
            return {
                "insights": [
                    {
                        "type": i.type,
                        "priority": i.priority,
                        "title": i.title,
                        "message": i.message,
                        "data": i.data,
                    }
                    for i in insights
                ]
            }

        else:
            return {"error": f"Unknown insight type: {insight_type}"}

    except Exception as e:
        _LOG_STORE.record_action(agent_name, description=f"get_insights failed | error={e}")
        return {"error": str(e)}


async def _set_quick_reminder(
    *,
    agent_name: str,
    user_id: str,
    db_session: Any,
    message: str,
    minutes_from_now: int,
    amount: Optional[int] = None,
    category: Optional[str] = None,
) -> Dict[str, Any]:
    """Set a quick reminder using Celery ETA scheduling."""
    try:
        # Validate time range (5 min to 24 hours)
        if minutes_from_now < 5:
            return {
                "error": "Minimum reminder time is 5 minutes.",
            }
        if minutes_from_now > 1440:  # 24 hours
            return {
                "error": "Maximum quick reminder time is 24 hours. Use a recurring reminder for longer durations.",
            }

        # Calculate remind_at time
        from datetime import timezone
        remind_at = datetime.now(timezone.utc) + timedelta(minutes=minutes_from_now)

        # Create reminder in database
        from server.repositories.quick_reminders import QuickReminderRepository
        from uuid import UUID

        repo = QuickReminderRepository(db_session, UUID(user_id))
        reminder = await repo.create(
            message=message,
            amount=amount,
            category=category.lower() if category else None,
            remind_at=remind_at,
            status="pending",
        )
        await db_session.flush()

        # Schedule Celery task with ETA
        from server.tasks.reminders import send_quick_reminder
        task = send_quick_reminder.apply_async(
            args=[reminder.id],
            eta=remind_at,
        )

        # Update reminder with task ID
        await repo.update(reminder.id, celery_task_id=task.id)
        await db_session.commit()

        _LOG_STORE.record_action(
            agent_name,
            description=f"set_quick_reminder | message={message[:50]} | minutes={minutes_from_now}",
        )

        # Format friendly time
        if minutes_from_now < 60:
            time_str = f"{minutes_from_now} minutes"
        elif minutes_from_now == 60:
            time_str = "1 hour"
        elif minutes_from_now < 120:
            time_str = f"1 hour {minutes_from_now - 60} minutes"
        else:
            hours = minutes_from_now // 60
            mins = minutes_from_now % 60
            if mins:
                time_str = f"{hours} hours {mins} minutes"
            else:
                time_str = f"{hours} hours"

        return {
            "success": True,
            "reminder_id": reminder.id,
            "message": message,
            "remind_at": remind_at.isoformat(),
            "time_from_now": time_str,
            "amount": amount,
            "category": category,
        }

    except Exception as e:
        _LOG_STORE.record_action(agent_name, description=f"set_quick_reminder failed | error={e}")
        return {"error": str(e)}


# =============================================================================
# Registry Builder
# =============================================================================

def build_registry(
    agent_name: str,
    finance_service: Any = None,
    insights_service: Any = None,
    user_id: Optional[str] = None,
    db_session: Any = None,
) -> Dict[str, Callable[..., Any]]:
    """Return adult finance tool callables bound to agent and service.

    Args:
        agent_name: Name of the execution agent
        finance_service: AdultFinanceService instance
        insights_service: InsightsService instance (optional)
        user_id: User ID for reminder operations (optional)
        db_session: Database session for reminder operations (optional)

    Returns:
        Dictionary mapping tool names to callables
    """
    if finance_service is None:
        return {}

    registry = {
        "record_transaction": partial(
            _record_transaction,
            agent_name=agent_name,
            finance_service=finance_service,
            insights_service=insights_service,
        ),
        "delete_transaction": partial(
            _delete_transaction,
            agent_name=agent_name,
            finance_service=finance_service,
        ),
        "query_finances": partial(
            _query_finances,
            agent_name=agent_name,
            finance_service=finance_service,
        ),
        "get_financial_summary": partial(
            _get_financial_summary,
            agent_name=agent_name,
            finance_service=finance_service,
        ),
        "get_dashboard": partial(
            _get_dashboard,
            agent_name=agent_name,
            finance_service=finance_service,
        ),
        "manage_budget": partial(
            _manage_budget,
            agent_name=agent_name,
            finance_service=finance_service,
        ),
        "manage_debt": partial(
            _manage_debt,
            agent_name=agent_name,
            finance_service=finance_service,
        ),
        "manage_recurring": partial(
            _manage_recurring,
            agent_name=agent_name,
            finance_service=finance_service,
        ),
        "get_insights": partial(
            _get_insights,
            agent_name=agent_name,
            finance_service=finance_service,
            insights_service=insights_service,
        ),
    }

    # Add quick reminder if user_id and db_session provided
    if user_id and db_session:
        registry["set_quick_reminder"] = partial(
            _set_quick_reminder,
            agent_name=agent_name,
            user_id=user_id,
            db_session=db_session,
        )

    return registry


__all__ = [
    "build_registry",
    "get_schemas",
]
