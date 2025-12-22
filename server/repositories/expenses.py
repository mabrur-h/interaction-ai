"""Expense repository for Wally Junior."""

import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, Sequence

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from server.database.models import Expense
from server.repositories.base import UserScopedRepository


class ExpenseRepository(UserScopedRepository[Expense]):
    """Repository for Expense operations (user-scoped)."""

    model = Expense

    async def log_expense(
        self,
        amount: int,
        category: str,
        description: Optional[str] = None,
        expense_date: Optional[datetime] = None,
    ) -> Expense:
        """Log a new expense.

        Args:
            amount: Amount in cents
            category: Expense category
            description: Optional description
            expense_date: When the expense occurred (defaults to now)

        Returns:
            The created Expense
        """
        kwargs = {
            "amount": amount,
            "category": category,
            "description": description,
        }
        if expense_date:
            kwargs["expense_date"] = expense_date
        return await self.create(**kwargs)

    async def get_expenses(
        self,
        limit: int = 50,
        offset: int = 0,
        category: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Sequence[Expense]:
        """Get expenses with optional filters.

        Args:
            limit: Maximum number of results
            offset: Number of results to skip
            category: Optional category filter
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            List of Expenses
        """
        query = select(Expense).where(Expense.user_id == self.user_id)

        if category:
            query = query.where(Expense.category == category)
        if start_date:
            query = query.where(Expense.expense_date >= start_date)
        if end_date:
            query = query.where(Expense.expense_date <= end_date)

        query = query.order_by(Expense.expense_date.desc()).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_total_spent(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> int:
        """Get total amount spent in a period.

        Args:
            start_date: Optional start date
            end_date: Optional end date

        Returns:
            Total amount in cents
        """
        query = select(func.coalesce(func.sum(Expense.amount), 0)).where(
            Expense.user_id == self.user_id
        )

        if start_date:
            query = query.where(Expense.expense_date >= start_date)
        if end_date:
            query = query.where(Expense.expense_date <= end_date)

        result = await self.session.execute(query)
        return result.scalar() or 0

    async def get_spending_by_category(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, int]:
        """Get spending grouped by category.

        Args:
            start_date: Optional start date
            end_date: Optional end date

        Returns:
            Dictionary mapping category to total amount in cents
        """
        query = select(
            Expense.category,
            func.sum(Expense.amount).label("total"),
        ).where(Expense.user_id == self.user_id)

        if start_date:
            query = query.where(Expense.expense_date >= start_date)
        if end_date:
            query = query.where(Expense.expense_date <= end_date)

        query = query.group_by(Expense.category)
        result = await self.session.execute(query)
        return {row.category: row.total for row in result.all()}

    async def get_expense_count(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> int:
        """Get count of expenses in a period.

        Args:
            start_date: Optional start date
            end_date: Optional end date

        Returns:
            Number of expenses
        """
        query = select(func.count(Expense.id)).where(Expense.user_id == self.user_id)

        if start_date:
            query = query.where(Expense.expense_date >= start_date)
        if end_date:
            query = query.where(Expense.expense_date <= end_date)

        result = await self.session.execute(query)
        return result.scalar() or 0
