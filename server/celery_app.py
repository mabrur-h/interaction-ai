"""Celery application configuration for background tasks."""

from celery import Celery

from server.config import get_settings

_settings = get_settings()

# Create Celery app
celery_app = Celery(
    "openpoke",
    broker=_settings.celery_broker_url,
    backend=_settings.celery_result_backend,
    include=[
        "server.tasks.triggers",
        "server.tasks.email_watcher",
        "server.tasks.maintenance",
    ],
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Result expiration
    result_expires=3600,  # Results expire after 1 hour

    # Worker settings
    worker_prefetch_multiplier=1,  # One task at a time for fair distribution
    worker_concurrency=4,  # Number of concurrent workers

    # Task routing
    task_default_queue="default",
    task_queues={
        "default": {},
        "triggers": {},
        "email": {},
        "maintenance": {},
    },

    # Beat schedule for periodic tasks
    beat_schedule={
        "check-due-triggers": {
            "task": "server.tasks.triggers.check_due_triggers",
            "schedule": 60.0,  # Every minute
            "options": {"queue": "triggers"},
        },
        "check-important-emails": {
            "task": "server.tasks.email_watcher.check_important_emails",
            "schedule": 300.0,  # Every 5 minutes
            "options": {"queue": "email"},
        },
        "cleanup-old-data": {
            "task": "server.tasks.maintenance.cleanup_old_data",
            "schedule": 86400.0,  # Daily
            "options": {"queue": "maintenance"},
        },
    },

    # Retry settings
    task_acks_late=True,  # Acknowledge after task completes
    task_reject_on_worker_lost=True,  # Requeue if worker dies
)


__all__ = ["celery_app"]
