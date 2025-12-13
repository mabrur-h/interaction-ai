"""Celery tasks for trigger management."""

import asyncio
from datetime import datetime, timezone

from server.celery_app import celery_app
from server.database.session import async_session_factory
from server.logging_config import logger
from server.repositories.triggers import TriggerRepository
from server.repositories.users import UserRepository
from server.services.v2 import TriggerService


def _run_async(coro):
    """Run async coroutine in sync context."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, queue="triggers", max_retries=3)
def check_due_triggers(self):
    """Check and execute all due triggers across all users."""
    logger.info("Checking for due triggers")

    async def _check():
        async with async_session_factory() as session:
            # Get all users with active triggers
            user_repo = UserRepository(session)
            users = await user_repo.get_all(limit=1000)

            total_executed = 0
            now = datetime.now(timezone.utc)

            for user in users:
                trigger_repo = TriggerRepository(session, user.id)
                trigger_service = TriggerService(trigger_repo)

                due_triggers = await trigger_service.get_due_triggers(before=now)

                for trigger in due_triggers:
                    # Queue individual trigger execution
                    execute_trigger.delay(
                        user_id=str(user.id),
                        trigger_id=trigger.id,
                        agent_name=trigger.agent_name,
                    )
                    total_executed += 1

            await session.commit()
            return total_executed

    try:
        count = _run_async(_check())
        logger.info(f"Queued {count} triggers for execution")
        return {"queued_triggers": count}
    except Exception as exc:
        logger.exception("Failed to check due triggers")
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True, queue="triggers", max_retries=3)
def execute_trigger(self, user_id: str, trigger_id: int, agent_name: str):
    """Execute a single trigger."""
    logger.info(f"Executing trigger {trigger_id} for user {user_id}")

    async def _execute():
        import uuid
        from server.database.session import async_session_factory
        from server.repositories.triggers import TriggerRepository
        from server.services.v2 import TriggerService

        async with async_session_factory() as session:
            user_uuid = uuid.UUID(user_id)
            trigger_repo = TriggerRepository(session, user_uuid)
            trigger_service = TriggerService(trigger_repo)

            trigger = await trigger_repo.get_one(trigger_id, agent_name)
            if not trigger:
                logger.warning(f"Trigger {trigger_id} not found")
                return None

            fired_at = datetime.now(timezone.utc)

            try:
                # TODO: Actually execute the trigger payload
                # This would call the execution agent with the trigger payload
                logger.info(
                    f"Trigger fired",
                    extra={
                        "trigger_id": trigger_id,
                        "agent_name": agent_name,
                        "payload": trigger.payload[:100],
                    },
                )

                # Schedule next occurrence (or mark complete if one-time)
                await trigger_service.schedule_next_occurrence(trigger, fired_at=fired_at)
                await session.commit()

                return {"status": "success", "trigger_id": trigger_id}

            except Exception as exc:
                logger.exception(f"Trigger execution failed: {trigger_id}")
                await trigger_service.record_failure(trigger, str(exc))
                await session.commit()
                raise

    try:
        return _run_async(_execute())
    except Exception as exc:
        logger.exception(f"Failed to execute trigger {trigger_id}")
        raise self.retry(exc=exc, countdown=300)  # Retry in 5 minutes


__all__ = ["check_due_triggers", "execute_trigger"]
