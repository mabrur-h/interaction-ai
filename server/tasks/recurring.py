"""Celery tasks for recurring transaction processing."""

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
def process_recurring_transactions(self) -> Dict[str, Any]:
    """Process all due recurring transactions for all users.

    This task runs daily (configured in celery_app.py beat_schedule) and:
    1. Finds all recurring transactions that are due
    2. Groups them by user
    3. Creates actual Transaction records from the templates
    4. Updates the next_due_date for each processed recurring

    Returns:
        Dict with total_processed, total_failed, and users count
    """
    logger.info("Starting recurring transaction processing")

    async def _process():
        from server.database.session import async_session_factory
        from server.database.models import User
        from server.repositories.transactions import TransactionRepository
        from server.repositories.budgets import BudgetRepository
        from server.repositories.debts import DebtRepository
        from server.repositories.recurring_transactions import (
            RecurringTransactionRepository,
            get_all_due_grouped_by_user,
        )
        from server.services.v2.adult_finance_service import AdultFinanceService
        from server.services.v2.currency_service import CurrencyService

        async with async_session_factory() as session:
            # Get all due recurring transactions grouped by user
            due_by_user = await get_all_due_grouped_by_user(session)

            if not due_by_user:
                logger.info("No due recurring transactions found")
                return {"total_processed": 0, "total_failed": 0, "users": 0}

            results = {
                "total_processed": 0,
                "total_failed": 0,
                "total_skipped": 0,
                "users": 0,
                "details": [],
            }

            for user_id, recurring_items in due_by_user.items():
                try:
                    # Get user
                    user = await session.get(User, user_id)
                    if not user:
                        logger.warning(f"User {user_id} not found, skipping")
                        continue

                    # Create repositories for this user
                    transaction_repo = TransactionRepository(session, user_id)
                    budget_repo = BudgetRepository(session, user_id)
                    debt_repo = DebtRepository(session, user_id)
                    recurring_repo = RecurringTransactionRepository(session, user_id)
                    currency_service = CurrencyService(session)

                    # Create service
                    service = AdultFinanceService(
                        transaction_repo=transaction_repo,
                        budget_repo=budget_repo,
                        debt_repo=debt_repo,
                        recurring_repo=recurring_repo,
                        currency_service=currency_service,
                        user=user,
                        auto_commit=False,  # We'll commit at the end
                    )

                    # Process due recurring transactions
                    user_result = await service.process_due_recurring_transactions()

                    results["total_processed"] += len(user_result["processed"])
                    results["total_failed"] += len(user_result["failed"])
                    results["total_skipped"] += len(user_result["skipped"])
                    results["users"] += 1

                    if user_result["processed"]:
                        results["details"].append({
                            "user_id": str(user_id),
                            "processed": len(user_result["processed"]),
                            "failed": len(user_result["failed"]),
                        })

                    logger.info(
                        f"Processed recurring for user {user_id}: "
                        f"{len(user_result['processed'])} processed, "
                        f"{len(user_result['failed'])} failed"
                    )

                except Exception as e:
                    logger.exception(f"Failed to process recurring for user {user_id}: {e}")
                    results["total_failed"] += len(recurring_items)

            # Commit all changes
            await session.commit()
            return results

    try:
        result = _run_async(_process())
        logger.info(
            f"Recurring transaction processing completed: "
            f"{result['total_processed']} processed, "
            f"{result['total_failed']} failed, "
            f"{result['users']} users"
        )
        return result
    except Exception as exc:
        logger.exception("Failed to process recurring transactions")
        raise self.retry(exc=exc, countdown=3600)  # Retry in 1 hour


__all__ = ["process_recurring_transactions"]
