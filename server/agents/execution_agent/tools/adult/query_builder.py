"""Safe query builder for adult finance operations.

This module provides a structured query system that:
- Accepts structured intent (not raw SQL) from the AI
- Validates all parameters against whitelists
- Always enforces user_id filtering at the repository level
- Returns properly scoped data only
"""

from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class QueryOperation(str, Enum):
    """Allowed query operations."""
    LIST = "list"
    SUM = "sum"
    AVERAGE = "average"
    COUNT = "count"
    COMPARE = "compare"
    TREND = "trend"


class DateRange(str, Enum):
    """Predefined date ranges."""
    TODAY = "today"
    THIS_WEEK = "this_week"
    THIS_MONTH = "this_month"
    LAST_30_DAYS = "last_30_days"
    LAST_MONTH = "last_month"
    LAST_3_MONTHS = "last_3_months"
    THIS_YEAR = "this_year"
    CUSTOM = "custom"


class GroupBy(str, Enum):
    """Allowed grouping options."""
    CATEGORY = "category"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    COUNTERPARTY = "counterparty"
    TYPE = "type"


class TransactionType(str, Enum):
    """Transaction types."""
    EXPENSE = "expense"
    INCOME = "income"
    TRANSFER = "transfer"
    ALL = "all"


# Allowed categories - can be extended
ALLOWED_CATEGORIES = {
    # Expenses
    "food", "groceries", "restaurants", "dining",
    "transport", "taxi", "fuel", "public_transport",
    "shopping", "clothes", "electronics",
    "entertainment", "subscriptions", "streaming",
    "utilities", "rent", "bills",
    "health", "medical", "pharmacy",
    "education", "books", "courses",
    "travel", "vacation",
    "gifts", "charity",
    "personal", "beauty", "fitness",
    "home", "furniture", "maintenance",
    "pets",
    "other",
    # Income
    "salary", "freelance", "business",
    "investments", "dividends", "interest",
    "refund", "cashback",
    "gift_received", "bonus",
}


class StructuredQuery(BaseModel):
    """Validated query structure from AI.

    This is what the AI produces - a structured intent that
    gets validated and executed safely.
    """
    operation: QueryOperation = Field(
        description="What to do: list, sum, average, count, compare, trend"
    )
    transaction_type: TransactionType = Field(
        default=TransactionType.ALL,
        description="Filter by transaction type"
    )
    date_range: DateRange = Field(
        default=DateRange.THIS_MONTH,
        description="Predefined date range"
    )
    custom_start: Optional[str] = Field(
        default=None,
        description="ISO date string for custom range start"
    )
    custom_end: Optional[str] = Field(
        default=None,
        description="ISO date string for custom range end"
    )
    categories: Optional[List[str]] = Field(
        default=None,
        description="Filter by categories"
    )
    amount_min: Optional[int] = Field(
        default=None,
        ge=0,
        description="Minimum amount filter (cents)"
    )
    amount_max: Optional[int] = Field(
        default=None,
        ge=0,
        description="Maximum amount filter (cents)"
    )
    search_text: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Search in description/counterparty"
    )
    group_by: Optional[GroupBy] = Field(
        default=None,
        description="How to group results"
    )
    compare_to: Optional[str] = Field(
        default=None,
        description="Compare to: previous_period, same_last_year"
    )
    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Max results to return"
    )

    @field_validator("categories")
    @classmethod
    def validate_categories(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate categories against whitelist."""
        if v is None:
            return None
        validated = []
        for cat in v:
            normalized = cat.lower().strip()
            if normalized in ALLOWED_CATEGORIES:
                validated.append(normalized)
        return validated if validated else None

    @field_validator("search_text")
    @classmethod
    def sanitize_search(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize search text."""
        if v is None:
            return None
        # Remove any SQL-like patterns
        sanitized = v.strip()[:100]
        # Block common SQL injection patterns
        dangerous_patterns = ["--", ";", "/*", "*/", "xp_", "exec", "union", "select"]
        for pattern in dangerous_patterns:
            if pattern.lower() in sanitized.lower():
                return None
        return sanitized


class FinanceQueryBuilder:
    """Builds safe queries from structured intents.

    Security:
    - user_id is ALWAYS from authenticated session (injected)
    - All parameters are validated against whitelists
    - No raw SQL ever reaches the database
    - Read-only operations only
    """

    def __init__(self, user_id: str):
        """Initialize with user ID (from session, not user input)."""
        self.user_id = user_id

    def parse_date_range(
        self,
        date_range: DateRange,
        custom_start: Optional[str] = None,
        custom_end: Optional[str] = None,
    ) -> tuple[datetime, datetime]:
        """Convert date range enum to actual dates."""
        now = datetime.now()
        end = now.replace(hour=23, minute=59, second=59)

        if date_range == DateRange.TODAY:
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            return start, end

        if date_range == DateRange.THIS_WEEK:
            start = now - timedelta(days=now.weekday())
            start = start.replace(hour=0, minute=0, second=0, microsecond=0)
            return start, end

        if date_range == DateRange.THIS_MONTH:
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            return start, end

        if date_range == DateRange.LAST_30_DAYS:
            start = (now - timedelta(days=30)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            return start, end

        if date_range == DateRange.LAST_MONTH:
            first_of_month = now.replace(day=1)
            end = first_of_month - timedelta(days=1)
            end = end.replace(hour=23, minute=59, second=59)
            start = end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            return start, end

        if date_range == DateRange.LAST_3_MONTHS:
            start = (now - timedelta(days=90)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            return start, end

        if date_range == DateRange.THIS_YEAR:
            start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            return start, end

        if date_range == DateRange.CUSTOM and custom_start and custom_end:
            try:
                start = datetime.fromisoformat(custom_start)
                end = datetime.fromisoformat(custom_end)
                # Enforce reasonable range (max 2 years)
                if (end - start).days > 730:
                    end = start + timedelta(days=730)
                return start, end
            except ValueError:
                pass

        # Default to this month
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return start, end

    def validate_query(self, query: StructuredQuery) -> Dict[str, Any]:
        """Validate query and return safe parameters.

        Returns a dict of validated parameters that can be
        safely passed to repository methods.
        """
        start_date, end_date = self.parse_date_range(
            query.date_range,
            query.custom_start,
            query.custom_end,
        )

        transaction_type = None
        if query.transaction_type != TransactionType.ALL:
            transaction_type = query.transaction_type.value

        return {
            "operation": query.operation.value,
            "start_date": start_date,
            "end_date": end_date,
            "transaction_type": transaction_type,
            "categories": query.categories,
            "amount_min": query.amount_min,
            "amount_max": query.amount_max,
            "search_text": query.search_text,
            "group_by": query.group_by.value if query.group_by else None,
            "compare_to": query.compare_to if query.compare_to in ["previous_period", "same_last_year"] else None,
            "limit": min(query.limit, 100),
        }

    def get_comparison_period(
        self,
        start_date: datetime,
        end_date: datetime,
        compare_to: str,
    ) -> tuple[datetime, datetime]:
        """Get comparison period dates."""
        period_days = (end_date - start_date).days

        if compare_to == "previous_period":
            comp_end = start_date - timedelta(days=1)
            comp_start = comp_end - timedelta(days=period_days)
            return comp_start, comp_end

        if compare_to == "same_last_year":
            comp_start = start_date.replace(year=start_date.year - 1)
            comp_end = end_date.replace(year=end_date.year - 1)
            return comp_start, comp_end

        # Fallback to previous period
        comp_end = start_date - timedelta(days=1)
        comp_start = comp_end - timedelta(days=period_days)
        return comp_start, comp_end


def create_query_from_dict(data: Dict[str, Any]) -> StructuredQuery:
    """Create a validated query from dict (from AI tool call).

    This is the main entry point - takes AI output and
    returns a validated, safe query structure.
    """
    return StructuredQuery(**data)


__all__ = [
    "ALLOWED_CATEGORIES",
    "DateRange",
    "FinanceQueryBuilder",
    "GroupBy",
    "QueryOperation",
    "StructuredQuery",
    "TransactionType",
    "create_query_from_dict",
]
