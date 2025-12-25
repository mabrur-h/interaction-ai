"""Celery tasks for payment reminders."""

import asyncio
from typing import Dict, Any

from server.celery_app import celery_app
from server.logging_config import logger


def _run_async(coro):
    """Run async coroutine in sync context."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, queue="default", max_retries=3)
def send_payment_reminders(self) -> Dict[str, Any]:
    """Send payment reminders for upcoming recurring transactions.

    This task runs daily (configured in celery_app.py beat_schedule) and:
    1. Finds all users with reminders enabled
    2. For each user, finds recurring transactions with reminder_days_before set
    3. Sends in-app reminders for transactions coming due
    4. Logs sent reminders to prevent duplicates

    Returns:
        Dict with sent count, users processed, and details
    """
    logger.info("Starting payment reminder processing")

    async def _send_reminders():
        from server.database.session import async_session_factory
        from server.repositories.recurring_transactions import RecurringTransactionRepository
        from server.repositories.reminder_logs import (
            ReminderLogRepository,
            get_users_with_reminders_enabled,
        )
        from server.services.v2.currency_service import CurrencyService
        from server.services.v2.reminder_service import ReminderService

        async with async_session_factory() as session:
            # Get all users with reminders enabled
            users = await get_users_with_reminders_enabled(session)

            if not users:
                logger.info("No users with reminders enabled")
                return {"sent": 0, "users": 0, "details": []}

            results = {
                "sent": 0,
                "failed": 0,
                "users": 0,
                "details": [],
            }

            for user in users:
                try:
                    # Create repositories for this user
                    recurring_repo = RecurringTransactionRepository(session, user.id)
                    reminder_log_repo = ReminderLogRepository(session, user.id)
                    currency_service = CurrencyService(session)

                    # Create reminder service
                    service = ReminderService(
                        recurring_repo=recurring_repo,
                        reminder_log_repo=reminder_log_repo,
                        currency_service=currency_service,
                        user=user,
                    )

                    # Get pending reminders for this user
                    pending = await service.get_pending_reminders()

                    if not pending:
                        continue

                    user_sent = 0
                    for reminder in pending:
                        success = await service.send_in_app_reminder(reminder)
                        if success:
                            user_sent += 1
                            results["sent"] += 1
                        else:
                            results["failed"] += 1

                    if user_sent > 0:
                        results["users"] += 1
                        results["details"].append({
                            "user_id": str(user.id),
                            "reminders_sent": user_sent,
                        })

                    logger.info(
                        f"Sent {user_sent} reminders for user {user.id}"
                    )

                except Exception as e:
                    logger.exception(f"Failed to process reminders for user {user.id}: {e}")

            # Commit all changes
            await session.commit()
            return results

    try:
        result = _run_async(_send_reminders())
        logger.info(
            f"Payment reminder processing completed: "
            f"{result['sent']} sent, "
            f"{result.get('failed', 0)} failed, "
            f"{result['users']} users"
        )
        return result
    except Exception as exc:
        logger.exception("Failed to send payment reminders")
        raise self.retry(exc=exc, countdown=3600)  # Retry in 1 hour


@celery_app.task(bind=True, queue="default", max_retries=2)
def send_quick_reminder(self, reminder_id: int) -> Dict[str, Any]:
    """Send a single quick reminder (scheduled via ETA).

    This task is scheduled with an ETA when the user creates a quick reminder.
    It fires at the scheduled time and notifies the user.

    Args:
        reminder_id: The QuickReminder ID to send

    Returns:
        Dict with status and reminder details
    """
    logger.info(f"Processing quick reminder {reminder_id}")

    async def _send_quick_reminder():
        from server.database.session import async_session_factory
        from server.database.models import User
        from server.repositories.quick_reminders import (
            get_reminder_by_id_system,
            mark_reminder_sent_system,
        )
        from server.services.v2.currency_service import CurrencyService

        async with async_session_factory() as session:
            # Get the reminder
            reminder = await get_reminder_by_id_system(session, reminder_id)

            if not reminder:
                logger.warning(f"Quick reminder {reminder_id} not found")
                return {"status": "not_found", "reminder_id": reminder_id}

            if reminder.status != "pending":
                logger.info(f"Quick reminder {reminder_id} already {reminder.status}")
                return {"status": "skipped", "reason": f"already_{reminder.status}"}

            # Format the notification message
            currency_service = CurrencyService(session)
            message = reminder.message

            if reminder.amount:
                user = await session.get(User, reminder.user_id)
                currency = user.primary_currency if user else "UZS"
                amount_str = currency_service.format_amount(reminder.amount, currency)
                notification = f"⏰ Reminder: {message} ({amount_str})"
            else:
                notification = f"⏰ Reminder: {message}"

            # Log the notification (in-app for now)
            # In the future, this could push to a notification system
            logger.info(f"Sending quick reminder to user {reminder.user_id}: {notification}")

            # Mark as sent
            await mark_reminder_sent_system(session, reminder_id)
            await session.commit()

            return {
                "status": "sent",
                "reminder_id": reminder_id,
                "user_id": str(reminder.user_id),
                "message": notification,
            }

    try:
        result = _run_async(_send_quick_reminder())
        logger.info(f"Quick reminder {reminder_id} result: {result['status']}")
        return result
    except Exception as exc:
        logger.exception(f"Failed to send quick reminder {reminder_id}")
        raise self.retry(exc=exc, countdown=60)  # Retry in 1 minute


__all__ = ["send_payment_reminders", "send_quick_reminder"]
