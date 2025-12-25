"""Reminder service for payment reminders."""

import logging
from datetime import date, timedelta
from typing import Any, Dict, List

from server.database.models import User, RecurringTransaction
from server.repositories.recurring_transactions import RecurringTransactionRepository
from server.repositories.reminder_logs import ReminderLogRepository
from server.services.v2.currency_service import CurrencyService

logger = logging.getLogger(__name__)


class ReminderService:
    """Service for handling payment reminder logic."""

    def __init__(
        self,
        recurring_repo: RecurringTransactionRepository,
        reminder_log_repo: ReminderLogRepository,
        currency_service: CurrencyService,
        user: User,
    ):
        """Initialize with repositories and user.

        Args:
            recurring_repo: Recurring transaction repository
            reminder_log_repo: Reminder log repository
            currency_service: Currency formatting service
            user: Current user
        """
        self.recurring_repo = recurring_repo
        self.reminder_log_repo = reminder_log_repo
        self.currency_service = currency_service
        self.user = user

    async def get_pending_reminders(self) -> List[Dict[str, Any]]:
        """Get recurring transactions that need reminders today.

        Checks all active recurring transactions with reminder_days_before set,
        and returns those where we're within the reminder window and haven't
        already sent a reminder today.

        Returns:
            List of reminder dicts with recurring transaction details
        """
        today = date.today()
        active_recurring = await self.recurring_repo.get_active()

        reminders = []
        for recurring in active_recurring:
            # Skip if no reminder configured
            if not recurring.reminder_days_before:
                continue

            # Calculate reminder date
            reminder_date = recurring.next_due_date - timedelta(
                days=recurring.reminder_days_before
            )

            # Check if we're in the reminder window
            if not (reminder_date <= today <= recurring.next_due_date):
                continue

            # Check if we already sent a reminder today
            already_sent = await self.reminder_log_repo.was_reminder_sent(
                recurring_id=recurring.id,
                reminder_date=today,
            )
            if already_sent:
                continue

            # Build reminder data
            template = recurring.template or {}
            currency = template.get("currency", self.user.primary_currency)
            amount = template.get("amount", 0)

            reminders.append({
                "recurring_id": recurring.id,
                "name": recurring.name,
                "amount": amount,
                "amount_formatted": self.currency_service.format_amount(amount, currency),
                "currency": currency,
                "category": template.get("category"),
                "type": template.get("type"),
                "due_date": recurring.next_due_date,
                "days_until_due": (recurring.next_due_date - today).days,
            })

        return reminders

    async def send_in_app_reminder(self, reminder: Dict[str, Any]) -> bool:
        """Create in-app notification for upcoming payment.

        Args:
            reminder: Reminder dict from get_pending_reminders()

        Returns:
            True if reminder was sent successfully
        """
        try:
            # Format the reminder message
            message = self._format_reminder_message(reminder)

            # Log that we sent the reminder (for deduplication)
            await self.reminder_log_repo.log_reminder(
                recurring_id=reminder["recurring_id"],
                reminder_date=date.today(),
                due_date=reminder["due_date"],
                channel="in_app",
            )

            logger.info(
                f"Sent in-app reminder for recurring {reminder['recurring_id']} "
                f"({reminder['name']}) to user {self.user.id}"
            )
            return True

        except Exception as e:
            logger.error(
                f"Failed to send reminder for recurring {reminder['recurring_id']}: {e}"
            )
            return False

    def _format_reminder_message(self, reminder: Dict[str, Any]) -> str:
        """Format a reminder into a user-friendly message.

        Args:
            reminder: Reminder dict

        Returns:
            Formatted message string
        """
        days = reminder["days_until_due"]
        name = reminder["name"]
        amount = reminder["amount_formatted"]

        if days == 0:
            return f"**{name}** ({amount}) is due today!"
        elif days == 1:
            return f"**{name}** ({amount}) is due tomorrow!"
        else:
            return f"**{name}** ({amount}) is due in {days} days."

    async def get_upcoming_payments(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get all upcoming payments in the next N days.

        Args:
            days: Number of days to look ahead

        Returns:
            List of upcoming recurring transactions
        """
        upcoming = await self.recurring_repo.get_upcoming(days)

        result = []
        for recurring in upcoming:
            template = recurring.template or {}
            currency = template.get("currency", self.user.primary_currency)
            amount = template.get("amount", 0)
            days_until = (recurring.next_due_date - date.today()).days

            result.append({
                "id": recurring.id,
                "name": recurring.name,
                "amount": amount,
                "amount_formatted": self.currency_service.format_amount(amount, currency),
                "currency": currency,
                "category": template.get("category"),
                "type": template.get("type"),
                "due_date": recurring.next_due_date.isoformat(),
                "days_until_due": days_until,
                "has_reminder": recurring.reminder_days_before is not None,
                "reminder_days_before": recurring.reminder_days_before,
            })

        return result
