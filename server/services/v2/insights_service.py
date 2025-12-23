"""Insights service for adult finance - patterns, summaries, and observations."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass

from server.database.models import User, Transaction
from server.repositories.transactions import TransactionRepository
from server.repositories.budgets import BudgetRepository
from server.services.v2.currency_service import CurrencyService


@dataclass
class Insight:
    """A single insight/observation."""

    type: str  # 'pattern', 'alert', 'tip', 'milestone', 'comparison'
    priority: int  # 1-5, higher = more important
    title: str
    message: str
    data: Optional[Dict[str, Any]] = None


class InsightsService:
    """Service for generating financial insights and observations."""

    def __init__(
        self,
        transaction_repo: TransactionRepository,
        budget_repo: BudgetRepository,
        currency_service: CurrencyService,
        user: User,
    ):
        self.transaction_repo = transaction_repo
        self.budget_repo = budget_repo
        self.currency_service = currency_service
        self.user = user
        self.currency = user.primary_currency

    # =========================================================================
    # Post-Transaction Insights
    # =========================================================================

    async def get_post_transaction_insights(
        self,
        transaction_type: str,
        amount: int,
        category: str,
    ) -> List[Insight]:
        """Generate insights after logging a transaction.

        Called immediately after a transaction is logged to provide
        relevant context and observations.
        """
        insights = []

        if transaction_type == "expense":
            # Check daily spending context
            daily_insight = await self._check_daily_spending(amount, category)
            if daily_insight:
                insights.append(daily_insight)

            # Check category trends
            category_insight = await self._check_category_trend(category, amount)
            if category_insight:
                insights.append(category_insight)

            # Check if unusual amount for category
            unusual_insight = await self._check_unusual_amount(category, amount)
            if unusual_insight:
                insights.append(unusual_insight)

        elif transaction_type == "income":
            # Check income frequency
            income_insight = await self._check_income_pattern()
            if income_insight:
                insights.append(income_insight)

        return sorted(insights, key=lambda x: x.priority, reverse=True)[:3]

    async def _check_daily_spending(
        self, amount: int, category: str
    ) -> Optional[Insight]:
        """Check today's spending context."""
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = datetime.now()

        transactions = await self.transaction_repo.get_by_date_range(
            today_start, today_end, "expense"
        )

        daily_total = sum(t.amount_primary for t in transactions)
        expense_count = len(transactions)

        if expense_count >= 5:
            return Insight(
                type="pattern",
                priority=3,
                title="Busy spending day",
                message=f"That's {expense_count} purchases today - {self._fmt(daily_total)} total",
                data={"count": expense_count, "total": daily_total},
            )

        if daily_total > 500_000:  # Over 500k
            return Insight(
                type="alert",
                priority=4,
                title="High spending day",
                message=f"You've spent {self._fmt(daily_total)} today",
                data={"total": daily_total},
            )

        return None

    async def _check_category_trend(
        self, category: str, amount: int
    ) -> Optional[Insight]:
        """Check spending trend in this category."""
        # Get last 30 days spending in category
        end = datetime.now()
        start = end - timedelta(days=30)

        transactions = await self.transaction_repo.get_by_date_range(
            start, end, "expense", category
        )

        if len(transactions) < 3:
            return None

        total = sum(t.amount_primary for t in transactions)
        avg = total // len(transactions)

        if amount > avg * 2:
            return Insight(
                type="pattern",
                priority=3,
                title=f"Above average for {category}",
                message=f"This is {amount // avg}x your usual {category} spend",
                data={"amount": amount, "average": avg},
            )

        return None

    async def _check_unusual_amount(
        self, category: str, amount: int
    ) -> Optional[Insight]:
        """Check if amount is unusual for this category."""
        # Get recent transactions in category
        end = datetime.now()
        start = end - timedelta(days=90)

        transactions = await self.transaction_repo.get_by_date_range(
            start, end, "expense", category, limit=50
        )

        if len(transactions) < 5:
            return None

        amounts = [t.amount_primary for t in transactions]
        avg = sum(amounts) // len(amounts)
        max_normal = max(amounts)

        if amount > max_normal * 1.5:
            return Insight(
                type="alert",
                priority=4,
                title=f"Unusually large {category} expense",
                message=f"This is {self._fmt(amount - avg)} more than your usual",
                data={"amount": amount, "max_previous": max_normal},
            )

        return None

    async def _check_income_pattern(self) -> Optional[Insight]:
        """Check income patterns."""
        # Get last 3 months of income
        end = datetime.now()
        start = end - timedelta(days=90)

        transactions = await self.transaction_repo.get_by_date_range(
            start, end, "income"
        )

        if len(transactions) == 0:
            return None

        total = sum(t.amount_primary for t in transactions)
        monthly_avg = total // 3

        return Insight(
            type="tip",
            priority=2,
            title="Income tracked",
            message=f"You average {self._fmt(monthly_avg)}/month",
            data={"monthly_average": monthly_avg},
        )

    # =========================================================================
    # Daily Summary
    # =========================================================================

    async def get_daily_summary(
        self, date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get summary for a specific day."""
        if date is None:
            date = datetime.now()

        day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = date.replace(hour=23, minute=59, second=59)

        # Get day totals
        totals = await self.transaction_repo.get_totals(day_start, day_end)
        by_category = await self.transaction_repo.get_summary_by_category(
            day_start, day_end, "expense"
        )

        # Get transactions
        transactions = await self.transaction_repo.get_by_date_range(
            day_start, day_end
        )

        # Get yesterday for comparison
        yesterday_start = day_start - timedelta(days=1)
        yesterday_end = day_end - timedelta(days=1)
        yesterday_totals = await self.transaction_repo.get_totals(
            yesterday_start, yesterday_end
        )

        # Generate insights
        insights = await self._generate_daily_insights(
            totals, by_category, len(transactions), yesterday_totals
        )

        return {
            "date": day_start.date().isoformat(),
            "income": totals["income"],
            "income_formatted": self._fmt(totals["income"]),
            "expenses": totals["expenses"],
            "expenses_formatted": self._fmt(totals["expenses"]),
            "net": totals["net"],
            "net_formatted": self._fmt(totals["net"]),
            "transaction_count": len(transactions),
            "by_category": {
                cat: {"amount": amt, "formatted": self._fmt(amt)}
                for cat, amt in by_category.items()
            },
            "top_category": max(by_category.items(), key=lambda x: x[1])[0]
            if by_category
            else None,
            "comparison": {
                "yesterday_expenses": yesterday_totals["expenses"],
                "change": totals["expenses"] - yesterday_totals["expenses"],
                "change_percent": self._percent_change(
                    yesterday_totals["expenses"], totals["expenses"]
                ),
            },
            "insights": [self._insight_to_dict(i) for i in insights],
        }

    async def _generate_daily_insights(
        self,
        totals: Dict[str, int],
        by_category: Dict[str, int],
        transaction_count: int,
        yesterday_totals: Dict[str, int],
    ) -> List[Insight]:
        """Generate insights for daily summary."""
        insights = []

        # Zero spend day
        if totals["expenses"] == 0 and transaction_count == 0:
            insights.append(
                Insight(
                    type="milestone",
                    priority=4,
                    title="No-spend day!",
                    message="You didn't spend anything today. Nice!",
                )
            )

        # Comparison to yesterday
        if yesterday_totals["expenses"] > 0:
            change_pct = self._percent_change(
                yesterday_totals["expenses"], totals["expenses"]
            )
            if change_pct <= -30:
                insights.append(
                    Insight(
                        type="tip",
                        priority=3,
                        title="Lower spending",
                        message=f"You spent {abs(int(change_pct))}% less than yesterday",
                    )
                )
            elif change_pct >= 50:
                insights.append(
                    Insight(
                        type="alert",
                        priority=3,
                        title="Higher spending",
                        message=f"You spent {int(change_pct)}% more than yesterday",
                    )
                )

        # Category dominance
        if by_category and totals["expenses"] > 0:
            top_cat = max(by_category.items(), key=lambda x: x[1])
            top_pct = round(top_cat[1] / totals["expenses"] * 100)
            if top_pct >= 70:
                insights.append(
                    Insight(
                        type="pattern",
                        priority=2,
                        title=f"{top_cat[0].title()} day",
                        message=f"{top_pct}% of spending was on {top_cat[0]}",
                        data={"category": top_cat[0], "percent": top_pct},
                    )
                )

        return sorted(insights, key=lambda x: x.priority, reverse=True)[:3]

    # =========================================================================
    # Weekly Summary
    # =========================================================================

    async def get_weekly_summary(
        self, week_start: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get summary for a week."""
        if week_start is None:
            today = datetime.now()
            # Go to Monday of this week
            week_start = today - timedelta(days=today.weekday())

        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        week_end = week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)

        # Get week totals
        totals = await self.transaction_repo.get_totals(week_start, week_end)
        by_category = await self.transaction_repo.get_summary_by_category(
            week_start, week_end, "expense"
        )

        # Get last week for comparison
        last_week_start = week_start - timedelta(days=7)
        last_week_end = week_end - timedelta(days=7)
        last_week_totals = await self.transaction_repo.get_totals(
            last_week_start, last_week_end
        )

        # Daily breakdown
        daily_totals = []
        for i in range(7):
            day_start = week_start + timedelta(days=i)
            day_end = day_start.replace(hour=23, minute=59, second=59)
            day_totals = await self.transaction_repo.get_totals(day_start, day_end)
            daily_totals.append(
                {
                    "day": day_start.strftime("%A"),
                    "date": day_start.date().isoformat(),
                    "expenses": day_totals["expenses"],
                    "formatted": self._fmt(day_totals["expenses"]),
                }
            )

        # Find busiest day
        busiest_day = max(daily_totals, key=lambda x: x["expenses"])

        # Budget status
        budgets = await self.budget_repo.get_active_budgets()
        budget_alerts = []
        for budget in budgets:
            spent = by_category.get(budget.category, 0)
            # Pro-rate monthly budget to weekly
            weekly_limit = budget.monthly_limit // 4
            if spent > weekly_limit:
                budget_alerts.append(
                    {
                        "category": budget.category,
                        "spent": spent,
                        "weekly_limit": weekly_limit,
                        "over_by": spent - weekly_limit,
                    }
                )

        # Generate insights
        insights = await self._generate_weekly_insights(
            totals, by_category, last_week_totals, daily_totals, budget_alerts
        )

        return {
            "week_start": week_start.date().isoformat(),
            "week_end": week_end.date().isoformat(),
            "income": totals["income"],
            "income_formatted": self._fmt(totals["income"]),
            "expenses": totals["expenses"],
            "expenses_formatted": self._fmt(totals["expenses"]),
            "net": totals["net"],
            "net_formatted": self._fmt(totals["net"]),
            "daily_average": totals["expenses"] // 7 if totals["expenses"] > 0 else 0,
            "daily_average_formatted": self._fmt(totals["expenses"] // 7)
            if totals["expenses"] > 0
            else self._fmt(0),
            "by_category": {
                cat: {"amount": amt, "formatted": self._fmt(amt)}
                for cat, amt in sorted(by_category.items(), key=lambda x: x[1], reverse=True)
            },
            "daily_breakdown": daily_totals,
            "busiest_day": busiest_day,
            "comparison": {
                "last_week_expenses": last_week_totals["expenses"],
                "change": totals["expenses"] - last_week_totals["expenses"],
                "change_percent": self._percent_change(
                    last_week_totals["expenses"], totals["expenses"]
                ),
            },
            "budget_alerts": budget_alerts,
            "insights": [self._insight_to_dict(i) for i in insights],
        }

    async def _generate_weekly_insights(
        self,
        totals: Dict[str, int],
        by_category: Dict[str, int],
        last_week_totals: Dict[str, int],
        daily_totals: List[Dict],
        budget_alerts: List[Dict],
    ) -> List[Insight]:
        """Generate insights for weekly summary."""
        insights = []

        # Week-over-week comparison
        if last_week_totals["expenses"] > 0:
            change_pct = self._percent_change(
                last_week_totals["expenses"], totals["expenses"]
            )
            if change_pct <= -20:
                insights.append(
                    Insight(
                        type="milestone",
                        priority=4,
                        title="Spending down!",
                        message=f"You spent {abs(int(change_pct))}% less than last week",
                    )
                )
            elif change_pct >= 30:
                insights.append(
                    Insight(
                        type="alert",
                        priority=4,
                        title="Spending up",
                        message=f"You spent {int(change_pct)}% more than last week",
                    )
                )

        # Budget alerts
        if budget_alerts:
            over_count = len(budget_alerts)
            insights.append(
                Insight(
                    type="alert",
                    priority=5,
                    title=f"{over_count} budget{'s' if over_count > 1 else ''} exceeded",
                    message=f"Over weekly limit for: {', '.join(b['category'] for b in budget_alerts)}",
                )
            )

        # Spending pattern
        non_zero_days = [d for d in daily_totals if d["expenses"] > 0]
        if len(non_zero_days) <= 3:
            insights.append(
                Insight(
                    type="pattern",
                    priority=3,
                    title="Concentrated spending",
                    message=f"Most spending was on {len(non_zero_days)} day{'s' if len(non_zero_days) > 1 else ''}",
                )
            )

        # Top category
        if by_category:
            top_cat = max(by_category.items(), key=lambda x: x[1])
            insights.append(
                Insight(
                    type="pattern",
                    priority=2,
                    title=f"Top category: {top_cat[0].title()}",
                    message=f"{self._fmt(top_cat[1])} this week",
                    data={"category": top_cat[0], "amount": top_cat[1]},
                )
            )

        return sorted(insights, key=lambda x: x.priority, reverse=True)[:4]

    # =========================================================================
    # Monthly Summary
    # =========================================================================

    async def get_monthly_summary(
        self, month: Optional[int] = None, year: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get summary for a month."""
        now = datetime.now()
        month = month or now.month
        year = year or now.year

        month_start = datetime(year, month, 1, 0, 0, 0)
        if month == 12:
            month_end = datetime(year + 1, 1, 1, 0, 0, 0) - timedelta(seconds=1)
        else:
            month_end = datetime(year, month + 1, 1, 0, 0, 0) - timedelta(seconds=1)

        # Get month totals
        totals = await self.transaction_repo.get_totals(month_start, month_end)
        by_category = await self.transaction_repo.get_summary_by_category(
            month_start, month_end, "expense"
        )
        income_by_category = await self.transaction_repo.get_summary_by_category(
            month_start, month_end, "income"
        )

        # Get last month for comparison
        if month == 1:
            last_month_start = datetime(year - 1, 12, 1, 0, 0, 0)
            last_month_end = datetime(year, 1, 1, 0, 0, 0) - timedelta(seconds=1)
        else:
            last_month_start = datetime(year, month - 1, 1, 0, 0, 0)
            last_month_end = month_start - timedelta(seconds=1)

        last_month_totals = await self.transaction_repo.get_totals(
            last_month_start, last_month_end
        )
        last_month_by_category = await self.transaction_repo.get_summary_by_category(
            last_month_start, last_month_end, "expense"
        )

        # Calculate days elapsed and days remaining
        days_in_month = (month_end - month_start).days + 1
        days_elapsed = min((now - month_start).days + 1, days_in_month)
        days_remaining = max(0, days_in_month - days_elapsed)

        # Projected spending
        if days_elapsed > 0:
            daily_rate = totals["expenses"] / days_elapsed
            projected_total = int(daily_rate * days_in_month)
        else:
            projected_total = 0

        # Category changes
        category_changes = {}
        all_categories = set(by_category.keys()) | set(last_month_by_category.keys())
        for cat in all_categories:
            current = by_category.get(cat, 0)
            previous = last_month_by_category.get(cat, 0)
            if previous > 0:
                change_pct = self._percent_change(previous, current)
                category_changes[cat] = {
                    "current": current,
                    "previous": previous,
                    "change_percent": change_pct,
                }

        # Budget status
        budgets = await self.budget_repo.get_active_budgets()
        budget_status = []
        for budget in budgets:
            spent = by_category.get(budget.category, 0)
            percent_used = round(spent / budget.monthly_limit * 100, 1) if budget.monthly_limit > 0 else 0
            remaining = max(0, budget.monthly_limit - spent)

            budget_status.append({
                "category": budget.category,
                "limit": budget.monthly_limit,
                "spent": spent,
                "remaining": remaining,
                "percent_used": percent_used,
                "over_budget": spent > budget.monthly_limit,
            })

        # Generate insights
        insights = await self._generate_monthly_insights(
            totals, by_category, last_month_totals, category_changes,
            budget_status, days_remaining, projected_total
        )

        return {
            "month": month,
            "year": year,
            "month_name": month_start.strftime("%B"),
            "income": totals["income"],
            "income_formatted": self._fmt(totals["income"]),
            "expenses": totals["expenses"],
            "expenses_formatted": self._fmt(totals["expenses"]),
            "net": totals["net"],
            "net_formatted": self._fmt(totals["net"]),
            "savings_rate": round(totals["net"] / totals["income"] * 100, 1)
            if totals["income"] > 0
            else 0,
            "days_elapsed": days_elapsed,
            "days_remaining": days_remaining,
            "daily_average": totals["expenses"] // days_elapsed if days_elapsed > 0 else 0,
            "projected_total": projected_total,
            "projected_formatted": self._fmt(projected_total),
            "by_category": {
                cat: {"amount": amt, "formatted": self._fmt(amt)}
                for cat, amt in sorted(by_category.items(), key=lambda x: x[1], reverse=True)
            },
            "income_sources": {
                cat: {"amount": amt, "formatted": self._fmt(amt)}
                for cat, amt in income_by_category.items()
            },
            "comparison": {
                "last_month_expenses": last_month_totals["expenses"],
                "change": totals["expenses"] - last_month_totals["expenses"],
                "change_percent": self._percent_change(
                    last_month_totals["expenses"], totals["expenses"]
                ),
            },
            "category_changes": category_changes,
            "budget_status": budget_status,
            "insights": [self._insight_to_dict(i) for i in insights],
        }

    async def _generate_monthly_insights(
        self,
        totals: Dict[str, int],
        by_category: Dict[str, int],
        last_month_totals: Dict[str, int],
        category_changes: Dict[str, Dict],
        budget_status: List[Dict],
        days_remaining: int,
        projected_total: int,
    ) -> List[Insight]:
        """Generate insights for monthly summary."""
        insights = []

        # Savings rate
        if totals["income"] > 0:
            savings_rate = round(totals["net"] / totals["income"] * 100, 1)
            if savings_rate >= 20:
                insights.append(
                    Insight(
                        type="milestone",
                        priority=5,
                        title=f"Great savings: {savings_rate}%",
                        message="You're keeping 20%+ of your income. Nice!",
                    )
                )
            elif savings_rate < 0:
                insights.append(
                    Insight(
                        type="alert",
                        priority=5,
                        title="Spending more than earning",
                        message=f"You're {abs(savings_rate)}% in the red this month",
                    )
                )

        # Month-over-month comparison
        if last_month_totals["expenses"] > 0:
            change_pct = self._percent_change(
                last_month_totals["expenses"], totals["expenses"]
            )
            if change_pct <= -15:
                insights.append(
                    Insight(
                        type="tip",
                        priority=3,
                        title="Lower than last month",
                        message=f"Spending down {abs(int(change_pct))}% vs last month",
                    )
                )

        # Budget alerts
        over_budget = [b for b in budget_status if b["over_budget"]]
        if over_budget:
            insights.append(
                Insight(
                    type="alert",
                    priority=5,
                    title=f"{len(over_budget)} over budget",
                    message=", ".join(b["category"] for b in over_budget),
                )
            )

        # Category spikes
        for cat, change in category_changes.items():
            if change["change_percent"] >= 50 and change["current"] > 100_000:
                insights.append(
                    Insight(
                        type="pattern",
                        priority=3,
                        title=f"{cat.title()} up {int(change['change_percent'])}%",
                        message=f"Spending more on {cat} than last month",
                        data={"category": cat, **change},
                    )
                )

        # Projection warning
        if days_remaining > 0 and projected_total > last_month_totals["expenses"] * 1.2:
            insights.append(
                Insight(
                    type="alert",
                    priority=4,
                    title="On track to overspend",
                    message=f"Projected {self._fmt(projected_total)} if current pace continues",
                )
            )

        return sorted(insights, key=lambda x: x.priority, reverse=True)[:5]

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _fmt(self, amount: int) -> str:
        """Format amount using currency service."""
        return self.currency_service.format_amount(amount, self.currency)

    def _percent_change(self, old: int, new: int) -> float:
        """Calculate percentage change."""
        if old == 0:
            return 100.0 if new > 0 else 0.0
        return round((new - old) / old * 100, 1)

    def _insight_to_dict(self, insight: Insight) -> Dict[str, Any]:
        """Convert Insight to dict."""
        return {
            "type": insight.type,
            "priority": insight.priority,
            "title": insight.title,
            "message": insight.message,
            "data": insight.data,
        }


__all__ = ["InsightsService", "Insight"]
