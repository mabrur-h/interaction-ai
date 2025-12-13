"""Celery tasks for maintenance operations."""

import asyncio
from datetime import datetime, timedelta, timezone

from server.celery_app import celery_app
from server.logging_config import logger


def _run_async(coro):
    """Run async coroutine in sync context."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, queue="maintenance", max_retries=3)
def cleanup_old_data(self):
    """Clean up old data across all users."""
    logger.info("Running maintenance cleanup")

    async def _cleanup():
        from server.database.session import async_session_factory
        from server.repositories.gmail_seen import GmailSeenRepository
        from server.repositories.users import UserRepository

        async with async_session_factory() as session:
            user_repo = UserRepository(session)
            users = await user_repo.get_all(limit=1000)

            total_cleaned = 0

            for user in users:
                # Clean up old Gmail seen entries (keep last 300)
                seen_repo = GmailSeenRepository(session, user.id)
                deleted = await seen_repo.cleanup_old_entries(keep_count=300)
                total_cleaned += deleted

                logger.debug(
                    f"Cleaned up data for user",
                    extra={"user_id": str(user.id), "deleted_seen": deleted},
                )

            await session.commit()
            return total_cleaned

    try:
        count = _run_async(_cleanup())
        logger.info(f"Maintenance cleanup completed: {count} records removed")
        return {"records_cleaned": count}
    except Exception as exc:
        logger.exception("Failed to run maintenance cleanup")
        raise self.retry(exc=exc, countdown=3600)  # Retry in 1 hour


@celery_app.task(bind=True, queue="maintenance")
def cleanup_expired_sessions(self):
    """Clean up expired user sessions."""
    logger.info("Cleaning up expired sessions")

    async def _cleanup():
        from sqlalchemy import delete
        from server.database.session import async_session_factory
        from server.database.models import Session

        async with async_session_factory() as session:
            now = datetime.now(timezone.utc)

            result = await session.execute(
                delete(Session).where(Session.expires_at < now)
            )
            await session.commit()

            return result.rowcount

    try:
        count = _run_async(_cleanup())
        logger.info(f"Cleaned up {count} expired sessions")
        return {"sessions_cleaned": count}
    except Exception as exc:
        logger.exception("Failed to cleanup expired sessions")
        raise


__all__ = ["cleanup_old_data", "cleanup_expired_sessions"]
