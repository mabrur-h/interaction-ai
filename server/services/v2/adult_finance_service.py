"""Adult finance service - main business logic for Poke."""

import logging
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from server.database.models import User, Transaction, Budget, Debt, RecurringTransaction
from server.repositories.transactions import TransactionRepository
from server.repositories.budgets import BudgetRepository
from server.repositories.debts import DebtRepository
from server.repositories.recurring_transactions import RecurringTransactionRepository
from server.services.v2.currency_service import CurrencyService
from server.utils.frequency import calculate_next_due_date

logger = logging.getLogger(__name__)


class AdultFinanceService:
    """Service for adult finance operations."""

    def __init__(
        self,
        transaction_repo: TransactionRepository,
        budget_repo: BudgetRepository,
        debt_repo: DebtRepository,
        recurring_repo: RecurringTransactionRepository,
        currency_service: CurrencyService,
        user: User,
        auto_commit: bool = False,
    ):
        """Initialize with repositories and user.

        Args:
            transaction_repo: Transaction repository
            budget_repo: Budget repository
            debt_repo: Debt repository
            recurring_repo: Recurring transaction repository
            currency_service: Currency conversion service
            user: Current user
            auto_commit: Whether to auto-commit after operations
        """
        self.transaction_repo = transaction_repo
        self.budget_repo = budget_repo
        self.debt_repo = debt_repo
        self.recurring_repo = recurring_repo
        self.currency_service = currency_service
        self.user = user
        self.auto_commit = auto_commit

    # =========================================================================
    # Transaction Operations
    # =========================================================================

    async def add_transaction(
        self,
        transaction_type: str,
        amount: int,
        category: str,
        description: Optional[str] = None,
        counterparty: Optional[str] = None,
        currency: Optional[str] = None,
        transaction_date: Optional[datetime] = None,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Add a new transaction.

        Args:
            transaction_type: 'expense', 'income', or 'transfer'
            amount: Amount in cents
            category: Category name
            description: Optional description
            counterparty: Optional who paid/received
            currency: Currency code (defaults to user's primary)
            transaction_date: Date of transaction (defaults to now)
            tags: Optional list of tags

        Returns:
            Dict with transaction details and any alerts
        """
        currency = currency or self.user.primary_currency
        transaction_date = transaction_date or datetime.now()

        # Convert to primary currency if different
        if currency != self.user.primary_currency:
            amount_primary, rate = await self.currency_service.convert(
                amount, currency, self.user.primary_currency
            )
        else:
            amount_primary = amount
            rate = Decimal("1.0")

        transaction = await self.transaction_repo.create(
            type=transaction_type,
            amount=amount,
            currency=currency,
            amount_primary=amount_primary,
            exchange_rate=float(rate) if rate else None,
            category=category,
            description=description,
            counterparty=counterparty,
            transaction_date=transaction_date,
            tags=tags or [],
        )

        if self.auto_commit:
            await self.transaction_repo.session.commit()

        # Check budget status if expense
        budget_alert = None
        if transaction_type == "expense":
            budget_alert = await self._check_budget_status(category)

        return {
            "id": transaction.id,
            "type": transaction_type,
            "amount": amount,
            "amount_formatted": self.currency_service.format_amount(amount, currency),
            "currency": currency,
            "category": category,
            "description": description,
            "budget_alert": budget_alert,
        }

    async def get_transactions(
        self,
        date_range: str = "this_month",
        transaction_type: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get transactions with filters.

        Args:
            date_range: 'today', 'this_week', 'this_month', 'last_30_days'
            transaction_type: Optional type filter
            category: Optional category filter
            limit: Max results

        Returns:
            List of transaction dicts
        """
        start_date, end_date = self._parse_date_range(date_range)

        transactions = await self.transaction_repo.get_by_date_range(
            start_date, end_date, transaction_type, category, limit
        )

        return [self._format_transaction(t) for t in transactions]

    async def get_summary(
        self,
        date_range: str = "this_month",
    ) -> Dict[str, Any]:
        """Get financial summary for a period.

        Args:
            date_range: Period to summarize

        Returns:
            Summary with income, expenses, net, by category
        """
        start_date, end_date = self._parse_date_range(date_range)

        totals = await self.transaction_repo.get_totals(start_date, end_date)
        by_category = await self.transaction_repo.get_summary_by_category(
            start_date, end_date, "expense"
        )

        currency = self.user.primary_currency

        return {
            "period": date_range,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "income": totals["income"],
            "income_formatted": self.currency_service.format_amount(
                totals["income"], currency
            ),
            "expenses": totals["expenses"],
            "expenses_formatted": self.currency_service.format_amount(
                totals["expenses"], currency
            ),
            "net": totals["net"],
            "net_formatted": self.currency_service.format_amount(
                totals["net"], currency
            ),
            "by_category": {
                cat: {
                    "amount": amt,
                    "formatted": self.currency_service.format_amount(amt, currency),
                }
                for cat, amt in by_category.items()
            },
            "savings_rate": (
                round(totals["net"] / totals["income"] * 100, 1)
                if totals["income"] > 0
                else 0
            ),
        }

    async def delete_transaction(self, transaction_id: int) -> bool:
        """Delete a transaction."""
        return await self.transaction_repo.delete(transaction_id)

    # =========================================================================
    # Budget Operations
    # =========================================================================

    async def set_budget(
        self,
        category: str,
        monthly_limit: int,
        alert_threshold: int = 80,
    ) -> Dict[str, Any]:
        """Set a budget for a category.

        Args:
            category: Category name
            monthly_limit: Monthly limit in cents
            alert_threshold: Alert percentage (0-100)

        Returns:
            Budget details
        """
        budget = await self.budget_repo.set_budget(
            category, monthly_limit, alert_threshold
        )

        if self.auto_commit:
            await self.budget_repo.session.commit()

        return {
            "id": budget.id,
            "category": category,
            "monthly_limit": monthly_limit,
            "monthly_limit_formatted": self.currency_service.format_amount(
                monthly_limit, self.user.primary_currency
            ),
            "alert_threshold": alert_threshold,
        }

    async def get_budgets(self) -> List[Dict[str, Any]]:
        """Get all active budgets with current spending."""
        budgets = await self.budget_repo.get_active_budgets()

        # Get current month spending
        start_date, end_date = self._parse_date_range("this_month")
        spending_by_category = await self.transaction_repo.get_summary_by_category(
            start_date, end_date, "expense"
        )

        result = []
        for budget in budgets:
            spent = spending_by_category.get(budget.category, 0)
            remaining = budget.monthly_limit - spent
            percent_used = (
                round(spent / budget.monthly_limit * 100, 1)
                if budget.monthly_limit > 0
                else 0
            )

            result.append({
                "id": budget.id,
                "category": budget.category,
                "monthly_limit": budget.monthly_limit,
                "monthly_limit_formatted": self.currency_service.format_amount(
                    budget.monthly_limit, self.user.primary_currency
                ),
                "spent": spent,
                "spent_formatted": self.currency_service.format_amount(
                    spent, self.user.primary_currency
                ),
                "remaining": remaining,
                "remaining_formatted": self.currency_service.format_amount(
                    max(0, remaining), self.user.primary_currency
                ),
                "percent_used": percent_used,
                "over_budget": remaining < 0,
                "alert_threshold": budget.alert_threshold,
                "alert_triggered": percent_used >= budget.alert_threshold,
            })

        return result

    async def delete_budget(self, category: str) -> bool:
        """Deactivate a budget."""
        return await self.budget_repo.deactivate(category)

    # =========================================================================
    # Debt Operations
    # =========================================================================

    async def add_debt(
        self,
        counterparty_name: str,
        debt_type: str,
        amount: int,
        currency: Optional[str] = None,
        due_date: Optional[date] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Add a new debt record.

        Args:
            counterparty_name: Name of person
            debt_type: 'lent' or 'borrowed'
            amount: Amount in cents
            currency: Currency code
            due_date: Optional due date
            notes: Optional notes

        Returns:
            Debt details
        """
        currency = currency or self.user.primary_currency

        debt = await self.debt_repo.create(
            counterparty_name=counterparty_name,
            type=debt_type,
            original_amount=amount,
            remaining_amount=amount,
            currency=currency,
            due_date=due_date,
            notes=notes,
        )

        if self.auto_commit:
            await self.debt_repo.session.commit()

        return {
            "id": debt.id,
            "counterparty": counterparty_name,
            "type": debt_type,
            "amount": amount,
            "amount_formatted": self.currency_service.format_amount(amount, currency),
            "currency": currency,
            "due_date": due_date.isoformat() if due_date else None,
        }

    async def get_debts(
        self,
        debt_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get active debts."""
        debts = await self.debt_repo.get_active_debts(debt_type)
        return [self._format_debt(d) for d in debts]

    async def record_debt_payment(
        self,
        debt_id: int,
        amount: int,
    ) -> Optional[Dict[str, Any]]:
        """Record a payment on a debt."""
        debt = await self.debt_repo.record_payment(debt_id, amount)
        if not debt:
            return None

        if self.auto_commit:
            await self.debt_repo.session.commit()

        return self._format_debt(debt)

    async def get_debt_summary(self) -> Dict[str, Any]:
        """Get debt summary."""
        summary = await self.debt_repo.get_summary()
        currency = self.user.primary_currency

        return {
            "total_lent": summary["total_lent"],
            "total_lent_formatted": self.currency_service.format_amount(
                summary["total_lent"], currency
            ),
            "total_borrowed": summary["total_borrowed"],
            "total_borrowed_formatted": self.currency_service.format_amount(
                summary["total_borrowed"], currency
            ),
            "net_position": summary["net_position"],
            "net_position_formatted": self.currency_service.format_amount(
                summary["net_position"], currency
            ),
        }

    # =========================================================================
    # Recurring Transaction Operations
    # =========================================================================

    async def add_recurring(
        self,
        name: str,
        transaction_type: str,
        amount: int,
        category: str,
        frequency: str,
        start_date: date,
        description: Optional[str] = None,
        counterparty: Optional[str] = None,
        currency: Optional[str] = None,
        reminder_days_before: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Add a recurring transaction template.

        Args:
            name: Name (e.g., "Netflix", "Salary")
            transaction_type: 'expense' or 'income'
            amount: Amount in cents
            category: Category
            frequency: 'daily', 'weekly', 'biweekly', 'monthly', 'yearly'
            start_date: When to start
            description: Optional description
            counterparty: Optional counterparty
            currency: Currency code
            reminder_days_before: Days before due date to send reminder

        Returns:
            Recurring transaction details
        """
        currency = currency or self.user.primary_currency

        template = {
            "type": transaction_type,
            "amount": amount,
            "currency": currency,
            "category": category,
            "description": description,
            "counterparty": counterparty,
        }

        recurring = await self.recurring_repo.create(
            name=name,
            template=template,
            frequency=frequency,
            next_due_date=start_date,
            reminder_days_before=reminder_days_before,
        )

        if self.auto_commit:
            await self.recurring_repo.session.commit()

        return {
            "id": recurring.id,
            "name": name,
            "type": transaction_type,
            "amount": amount,
            "amount_formatted": self.currency_service.format_amount(amount, currency),
            "frequency": frequency,
            "next_due_date": start_date.isoformat(),
            "reminder_days_before": reminder_days_before,
        }

    async def get_recurring(self) -> List[Dict[str, Any]]:
        """Get all active recurring transactions."""
        recurring = await self.recurring_repo.get_active()
        return [self._format_recurring(r) for r in recurring]

    async def get_monthly_recurring_total(self) -> Dict[str, Any]:
        """Get total monthly recurring expenses and income."""
        expenses = await self.recurring_repo.get_monthly_total("expense")
        income = await self.recurring_repo.get_monthly_total("income")
        currency = self.user.primary_currency

        return {
            "monthly_recurring_expenses": expenses,
            "monthly_recurring_expenses_formatted": self.currency_service.format_amount(
                expenses, currency
            ),
            "monthly_recurring_income": income,
            "monthly_recurring_income_formatted": self.currency_service.format_amount(
                income, currency
            ),
            "net_recurring": income - expenses,
            "net_recurring_formatted": self.currency_service.format_amount(
                income - expenses, currency
            ),
        }

    async def process_due_recurring_transactions(self) -> Dict[str, Any]:
        """Process all due recurring transactions for this user.

        This method is called by the scheduled task to auto-generate transactions
        from recurring templates when they become due.

        Returns:
            Dict with processed, failed, and skipped counts
        """
        today = date.today()
        due_items = await self.recurring_repo.get_due_today()
        results: Dict[str, Any] = {"processed": [], "failed": [], "skipped": []}

        for recurring in due_items:
            try:
                # Idempotency check - skip if already processed today
                if recurring.last_processed_date == today:
                    results["skipped"].append(recurring.id)
                    logger.debug(
                        f"Skipping recurring {recurring.id} - already processed today"
                    )
                    continue

                # Create transaction from template
                template = recurring.template or {}
                currency = template.get("currency", self.user.primary_currency)
                amount = template.get("amount", 0)

                # Convert to primary currency if different
                if currency != self.user.primary_currency:
                    amount_primary, rate = await self.currency_service.convert(
                        amount, currency, self.user.primary_currency
                    )
                else:
                    amount_primary = amount
                    rate = Decimal("1.0")

                # Create the transaction
                transaction = await self.transaction_repo.create(
                    type=template.get("type", "expense"),
                    amount=amount,
                    currency=currency,
                    amount_primary=amount_primary,
                    exchange_rate=float(rate) if rate else None,
                    category=template.get("category", "uncategorized"),
                    description=template.get("description"),
                    counterparty=template.get("counterparty"),
                    transaction_date=datetime.now(),
                    is_recurring=True,
                    recurring_id=recurring.id,
                    tags=[],
                )

                # Calculate and set next due date
                next_due = calculate_next_due_date(recurring.next_due_date, recurring.frequency)
                await self.recurring_repo.mark_processed(recurring.id, next_due)

                results["processed"].append({
                    "recurring_id": recurring.id,
                    "recurring_name": recurring.name,
                    "transaction_id": transaction.id,
                    "amount": amount,
                    "type": template.get("type"),
                })
                logger.info(
                    f"Processed recurring {recurring.id} ({recurring.name}) -> transaction {transaction.id}"
                )

            except Exception as e:
                logger.error(f"Failed to process recurring {recurring.id}: {e}")
                results["failed"].append({
                    "id": recurring.id,
                    "name": recurring.name,
                    "error": str(e),
                })

        return results

    # =========================================================================
    # Dashboard / Overview
    # =========================================================================

    async def get_dashboard(self) -> Dict[str, Any]:
        """Get complete financial dashboard."""
        # Get summaries
        month_summary = await self.get_summary("this_month")
        week_summary = await self.get_summary("this_week")

        # Get budgets with status
        budgets = await self.get_budgets()
        over_budget_count = sum(1 for b in budgets if b["over_budget"])

        # Get debt summary
        debt_summary = await self.get_debt_summary()

        # Get recurring totals
        recurring_totals = await self.get_monthly_recurring_total()

        # Recent transactions
        recent = await self.transaction_repo.get_recent(5)

        return {
            "month": month_summary,
            "week": week_summary,
            "budgets": {
                "count": len(budgets),
                "over_budget_count": over_budget_count,
                "items": budgets[:5],  # Top 5
            },
            "debts": debt_summary,
            "recurring": recurring_totals,
            "recent_transactions": [self._format_transaction(t) for t in recent],
        }

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _parse_date_range(self, date_range: str) -> tuple:
        """Parse date range string to start/end dates."""
        today = datetime.now().replace(hour=23, minute=59, second=59)

        if date_range == "today":
            start = today.replace(hour=0, minute=0, second=0)
            return start, today

        if date_range == "this_week":
            start = today - timedelta(days=today.weekday())
            start = start.replace(hour=0, minute=0, second=0)
            return start, today

        if date_range == "this_month":
            start = today.replace(day=1, hour=0, minute=0, second=0)
            return start, today

        if date_range == "last_30_days":
            start = today - timedelta(days=30)
            start = start.replace(hour=0, minute=0, second=0)
            return start, today

        if date_range == "last_month":
            first_of_this_month = today.replace(day=1)
            end = first_of_this_month - timedelta(days=1)
            start = end.replace(day=1, hour=0, minute=0, second=0)
            return start, end.replace(hour=23, minute=59, second=59)

        # Default to this month
        start = today.replace(day=1, hour=0, minute=0, second=0)
        return start, today

    def _format_transaction(self, t: Transaction) -> Dict[str, Any]:
        """Format transaction for API response."""
        return {
            "id": t.id,
            "type": t.type,
            "amount": t.amount,
            "amount_formatted": self.currency_service.format_amount(t.amount, t.currency),
            "currency": t.currency,
            "amount_primary": t.amount_primary,
            "category": t.category,
            "description": t.description,
            "counterparty": t.counterparty,
            "transaction_date": t.transaction_date.isoformat(),
            "is_recurring": t.is_recurring,
            "tags": t.tags or [],
        }

    def _format_debt(self, d: Debt) -> Dict[str, Any]:
        """Format debt for API response."""
        return {
            "id": d.id,
            "counterparty": d.counterparty_name,
            "type": d.type,
            "original_amount": d.original_amount,
            "remaining_amount": d.remaining_amount,
            "remaining_formatted": self.currency_service.format_amount(
                d.remaining_amount, d.currency
            ),
            "currency": d.currency,
            "due_date": d.due_date.isoformat() if d.due_date else None,
            "status": d.status,
            "notes": d.notes,
            "percent_paid": round(
                (d.original_amount - d.remaining_amount) / d.original_amount * 100, 1
            ) if d.original_amount > 0 else 0,
        }

    def _format_recurring(self, r: RecurringTransaction) -> Dict[str, Any]:
        """Format recurring transaction for API response."""
        template = r.template or {}
        currency = template.get("currency", self.user.primary_currency)
        amount = template.get("amount", 0)

        return {
            "id": r.id,
            "name": r.name,
            "type": template.get("type"),
            "amount": amount,
            "amount_formatted": self.currency_service.format_amount(amount, currency),
            "currency": currency,
            "category": template.get("category"),
            "frequency": r.frequency,
            "next_due_date": r.next_due_date.isoformat() if r.next_due_date else None,
            "is_active": r.is_active,
        }

    async def _check_budget_status(self, category: str) -> Optional[Dict[str, Any]]:
        """Check if spending in category is over/near budget."""
        budget = await self.budget_repo.get_by_category(category)
        if not budget or not budget.is_active:
            return None

        # Get current month spending
        start_date, end_date = self._parse_date_range("this_month")
        spending = await self.transaction_repo.get_summary_by_category(
            start_date, end_date, "expense"
        )

        spent = spending.get(category, 0)
        percent_used = (
            round(spent / budget.monthly_limit * 100, 1)
            if budget.monthly_limit > 0
            else 0
        )

        if percent_used >= 100:
            return {
                "status": "over_budget",
                "message": f"You're over budget for {category}!",
                "percent_used": percent_used,
            }
        elif percent_used >= budget.alert_threshold:
            return {
                "status": "near_limit",
                "message": f"You've used {percent_used}% of your {category} budget",
                "percent_used": percent_used,
            }

        return None
