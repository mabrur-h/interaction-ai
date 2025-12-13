"""Bridge between V2 database OAuth connections and V1 global singletons.

This module syncs the user's OAuth connections from the PostgreSQL database
to the in-memory global singletons used by execution agents.
"""

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from server.logging_config import logger
from server.repositories.oauth_connections import OAuthConnectionRepository


async def sync_oauth_connections_for_user(
    session: AsyncSession,
    user_id: uuid.UUID,
) -> None:
    """Sync OAuth connections from database to V1 global singletons.

    This should be called before executing agents to ensure they have
    access to the user's connected services.

    Args:
        session: Database session
        user_id: The user's UUID
    """
    oauth_repo = OAuthConnectionRepository(session, user_id)

    # Sync Gmail connection
    gmail_conn = await oauth_repo.get_gmail_connection()
    if gmail_conn and gmail_conn.status == "active" and gmail_conn.composio_user_id:
        _set_gmail_user_id(gmail_conn.composio_user_id)
        logger.info(
            "Synced Gmail connection from DB",
            extra={"user_id": str(user_id), "composio_user_id": gmail_conn.composio_user_id},
        )
    else:
        logger.debug(
            "No active Gmail connection in DB",
            extra={"user_id": str(user_id)},
        )

    # Sync Calendar connection
    calendar_conn = await oauth_repo.get_calendar_connection()
    if calendar_conn and calendar_conn.status == "active" and calendar_conn.composio_user_id:
        _set_calendar_user_id(calendar_conn.composio_user_id)
        logger.info(
            "Synced Calendar connection from DB",
            extra={"user_id": str(user_id), "composio_user_id": calendar_conn.composio_user_id},
        )
    else:
        logger.debug(
            "No active Calendar connection in DB",
            extra={"user_id": str(user_id)},
        )


def _set_gmail_user_id(composio_user_id: Optional[str]) -> None:
    """Set the Gmail user ID in the V1 global singleton."""
    try:
        from server.services.gmail.client import _set_active_gmail_user_id
        _set_active_gmail_user_id(composio_user_id)
    except ImportError:
        logger.warning("Could not import Gmail client to set user ID")


def _set_calendar_user_id(composio_user_id: Optional[str]) -> None:
    """Set the Calendar user ID in the V1 global singleton."""
    try:
        from server.services.calendar.client import _set_active_calendar_user_id
        _set_active_calendar_user_id(composio_user_id)
    except ImportError:
        logger.warning("Could not import Calendar client to set user ID")


__all__ = ["sync_oauth_connections_for_user"]
