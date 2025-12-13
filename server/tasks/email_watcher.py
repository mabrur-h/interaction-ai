"""Celery tasks for email importance watching."""

import asyncio

from server.celery_app import celery_app
from server.logging_config import logger


def _run_async(coro):
    """Run async coroutine in sync context."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, queue="email", max_retries=3)
def check_important_emails(self):
    """Check for important emails across all users with Gmail connected."""
    logger.info("Checking for important emails")

    async def _check():
        from server.database.session import async_session_factory
        from server.repositories.oauth_connections import OAuthConnectionRepository
        from server.repositories.gmail_seen import GmailSeenRepository
        from server.repositories.users import UserRepository

        async with async_session_factory() as session:
            user_repo = UserRepository(session)
            users = await user_repo.get_all(limit=1000)

            total_checked = 0

            for user in users:
                oauth_repo = OAuthConnectionRepository(session, user.id)
                gmail_conn = await oauth_repo.get_gmail_connection()

                if not gmail_conn or gmail_conn.status != "active":
                    continue

                # User has active Gmail - check for new important emails
                seen_repo = GmailSeenRepository(session, user.id)

                try:
                    # TODO: Implement actual email importance checking
                    # This would:
                    # 1. Fetch recent emails using Composio
                    # 2. Filter out already-seen message IDs
                    # 3. Classify importance using LLM
                    # 4. Notify user of important emails
                    # 5. Mark messages as seen

                    total_checked += 1
                    logger.debug(
                        f"Checked emails for user",
                        extra={"user_id": str(user.id)},
                    )

                except Exception as exc:
                    logger.warning(
                        f"Failed to check emails for user",
                        extra={"user_id": str(user.id), "error": str(exc)},
                    )

            await session.commit()
            return total_checked

    try:
        count = _run_async(_check())
        logger.info(f"Checked emails for {count} users")
        return {"users_checked": count}
    except Exception as exc:
        logger.exception("Failed to check important emails")
        raise self.retry(exc=exc, countdown=300)


__all__ = ["check_important_emails"]
