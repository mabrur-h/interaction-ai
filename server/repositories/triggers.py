"""Trigger repository."""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional, Sequence

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from server.database.models import Trigger
from server.repositories.base import UserScopedRepository


class TriggerRepository(UserScopedRepository[Trigger]):
    """Repository for Trigger operations (user-scoped)."""

    model = Trigger

    async def get_active_triggers(self) -> Sequence[Trigger]:
        """Get all active triggers for the current user.

        Returns:
            List of active Triggers
        """
        result = await self.session.execute(
            select(Trigger)
            .where(
                Trigger.user_id == self.user_id,
                Trigger.status == "active",
            )
            .order_by(Trigger.next_trigger)
        )
        return result.scalars().all()

    async def get_due_triggers(
        self, before: datetime, agent_name: Optional[str] = None
    ) -> Sequence[Trigger]:
        """Get triggers that are due to run.

        Args:
            before: Get triggers with next_trigger before this time
            agent_name: Optional filter by agent name

        Returns:
            List of due Triggers
        """
        query = select(Trigger).where(
            Trigger.user_id == self.user_id,
            Trigger.status == "active",
            Trigger.next_trigger.isnot(None),
            Trigger.next_trigger <= before,
        )
        if agent_name:
            query = query.where(Trigger.agent_name == agent_name)
        query = query.order_by(Trigger.next_trigger, Trigger.id)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_agent_name(self, agent_name: str) -> Sequence[Trigger]:
        """Get all triggers for a specific agent.

        Args:
            agent_name: The agent name

        Returns:
            List of Triggers for the agent
        """
        result = await self.session.execute(
            select(Trigger)
            .where(
                Trigger.user_id == self.user_id,
                Trigger.agent_name == agent_name,
            )
            .order_by(
                Trigger.next_trigger.is_(None),  # NULLs last
                Trigger.next_trigger,
            )
        )
        return result.scalars().all()

    async def get_one(self, trigger_id: int, agent_name: str) -> Optional[Trigger]:
        """Get a specific trigger by ID and agent name.

        Args:
            trigger_id: The trigger ID
            agent_name: The agent name

        Returns:
            The Trigger or None if not found
        """
        result = await self.session.execute(
            select(Trigger).where(
                Trigger.id == trigger_id,
                Trigger.user_id == self.user_id,
                Trigger.agent_name == agent_name,
            )
        )
        return result.scalar_one_or_none()

    async def create_trigger(
        self,
        agent_name: str,
        payload: str,
        start_time: Optional[datetime] = None,
        next_trigger: Optional[datetime] = None,
        recurrence_rule: Optional[str] = None,
        timezone: Optional[str] = None,
        status: str = "active",
        last_error: Optional[str] = None,
    ) -> Trigger:
        """Create a new trigger.

        Args:
            agent_name: Name of the agent to trigger
            payload: Task payload
            start_time: When the trigger starts
            next_trigger: Next scheduled run time
            recurrence_rule: RRULE for recurring triggers
            timezone: Timezone for the trigger
            status: Initial status (default: active)
            last_error: Initial error message (default: None)

        Returns:
            The created Trigger
        """
        return await self.create(
            agent_name=agent_name,
            payload=payload,
            start_time=start_time,
            next_trigger=next_trigger,
            recurrence_rule=recurrence_rule,
            timezone=timezone,
            status=status,
            last_error=last_error,
        )

    async def update_trigger(
        self, trigger_id: int, agent_name: str, fields: Dict[str, Any]
    ) -> bool:
        """Update a trigger with arbitrary fields.

        Args:
            trigger_id: The trigger ID
            agent_name: The agent name
            fields: Dictionary of field names to values

        Returns:
            True if updated, False if not found
        """
        if not fields:
            return False

        # Check if trigger exists and belongs to this user/agent
        existing = await self.get_one(trigger_id, agent_name)
        if not existing:
            return False

        await self.update(trigger_id, **fields)
        return True

    async def update_next_trigger(
        self, trigger_id: int, next_trigger: Optional[datetime]
    ) -> Optional[Trigger]:
        """Update the next trigger time.

        Args:
            trigger_id: The trigger ID
            next_trigger: The new next trigger time (None to deactivate)

        Returns:
            The updated Trigger or None if not found
        """
        updates: Dict[str, Any] = {"next_trigger": next_trigger}
        if next_trigger is None:
            updates["status"] = "completed"
        return await self.update(trigger_id, **updates)

    async def mark_completed(self, trigger_id: int, agent_name: str) -> bool:
        """Mark a trigger as completed.

        Args:
            trigger_id: The trigger ID
            agent_name: The agent name

        Returns:
            True if updated, False if not found
        """
        return await self.update_trigger(
            trigger_id,
            agent_name,
            {
                "status": "completed",
                "next_trigger": None,
                "last_error": None,
            },
        )

    async def set_error(
        self, trigger_id: int, agent_name: str, error: str
    ) -> bool:
        """Set an error on a trigger.

        Args:
            trigger_id: The trigger ID
            agent_name: The agent name
            error: The error message

        Returns:
            True if updated, False if not found
        """
        return await self.update_trigger(
            trigger_id, agent_name, {"last_error": error}
        )

    async def deactivate(self, trigger_id: int) -> Optional[Trigger]:
        """Deactivate a trigger.

        Args:
            trigger_id: The trigger ID

        Returns:
            The updated Trigger or None if not found
        """
        return await self.update(trigger_id, status="inactive")

    async def clear_all(self) -> int:
        """Delete all triggers for the current user.

        Returns:
            Number of deleted triggers
        """
        result = await self.session.execute(
            delete(Trigger).where(Trigger.user_id == self.user_id)
        )
        return result.rowcount
