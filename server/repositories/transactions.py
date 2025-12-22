"""Transaction repository for adult finance."""

from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Sequence

from sqlalchemy import select, func, and_, case
from sqlalchemy.ext.asyncio import AsyncSession

from server.database.models import Transaction
from server.repositories.base import UserScopedRepository


class TransactionRepository(UserScopedRepository[Transaction]):
    """Repository for Transaction operations (user-scoped)."""

    model = Transaction

    async def get_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        transaction_type: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 100,
    ) -> Sequence[Transaction]:
        """Get transactions within a date range.

        Args:
            start_date: Start of the range
            end_date: End of the range
            transaction_type: Optional filter by type (expense/income/transfer)
            category: Optional filter by category
            limit: Maximum results

        Returns:
            List of transactions
        """
        query = (
            select(Transaction)
            .where(
                Transaction.user_id == self.user_id,
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date <= end_date,
            )
            .order_by(Transaction.transaction_date.desc())
            .limit(limit)
        )

        if transaction_type:
            query = query.where(Transaction.type == transaction_type)
        if category:
            query = query.where(Transaction.category == category)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_summary_by_category(
        self,
        start_date: datetime,
        end_date: datetime,
        transaction_type: str = "expense",
    ) -> Dict[str, int]:
        """Get spending/income summary grouped by category.

        Args:
            start_date: Start of the range
            end_date: End of the range
            transaction_type: Type to summarize (expense/income)

        Returns:
            Dict of category -> total amount (in primary currency)
        """
        query = (
            select(
                Transaction.category,
                func.sum(Transaction.amount_primary).label("total"),
            )
            .where(
                Transaction.user_id == self.user_id,
                Transaction.type == transaction_type,
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date <= end_date,
            )
            .group_by(Transaction.category)
        )

        result = await self.session.execute(query)
        return {row.category: row.total or 0 for row in result.all()}

    async def get_totals(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, int]:
        """Get total income, expenses, and net for a period.

        Args:
            start_date: Start of the range
            end_date: End of the range

        Returns:
            Dict with 'income', 'expenses', 'net' totals (in primary currency)
        """
        query = (
            select(
                func.sum(
                    case(
                        (Transaction.type == "income", Transaction.amount_primary),
                        else_=0,
                    )
                ).label("income"),
                func.sum(
                    case(
                        (Transaction.type == "expense", Transaction.amount_primary),
                        else_=0,
                    )
                ).label("expenses"),
            )
            .where(
                Transaction.user_id == self.user_id,
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date <= end_date,
            )
        )

        result = await self.session.execute(query)
        row = result.one()
        income = row.income or 0
        expenses = row.expenses or 0

        return {
            "income": income,
            "expenses": expenses,
            "net": income - expenses,
        }

    async def get_category_count(self) -> int:
        """Get count of unique categories used by user."""
        query = (
            select(func.count(func.distinct(Transaction.category)))
            .where(Transaction.user_id == self.user_id)
        )
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def get_transaction_count(
        self,
        transaction_type: Optional[str] = None,
    ) -> int:
        """Get total count of transactions."""
        query = select(func.count(Transaction.id)).where(
            Transaction.user_id == self.user_id
        )
        if transaction_type:
            query = query.where(Transaction.type == transaction_type)

        result = await self.session.execute(query)
        return result.scalar() or 0

    async def search(
        self,
        search_text: str,
        limit: int = 20,
    ) -> Sequence[Transaction]:
        """Search transactions by description or counterparty.

        Args:
            search_text: Text to search for
            limit: Maximum results

        Returns:
            List of matching transactions
        """
        pattern = f"%{search_text}%"
        query = (
            select(Transaction)
            .where(
                Transaction.user_id == self.user_id,
                (
                    Transaction.description.ilike(pattern)
                    | Transaction.counterparty.ilike(pattern)
                ),
            )
            .order_by(Transaction.transaction_date.desc())
            .limit(limit)
        )

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_recent(self, limit: int = 10) -> Sequence[Transaction]:
        """Get most recent transactions."""
        query = (
            select(Transaction)
            .where(Transaction.user_id == self.user_id)
            .order_by(Transaction.transaction_date.desc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        return result.scalars().all()
