"""Async trigger service using PostgreSQL repository."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Sequence

from zoneinfo import ZoneInfo

from server.database.models import Trigger
from server.logging_config import logger
from server.repositories.triggers import TriggerRepository
from server.services.triggers.utils import (
    build_recurrence,
    coerce_start_datetime,
    load_rrule,
    normalize_status,
    resolve_timezone,
    utc_now,
)


MISSED_TRIGGER_GRACE_PERIOD = timedelta(minutes=5)


class TriggerService:
    """High-level async trigger management with recurrence awareness.

    This is the v2 async version that uses TriggerRepository (PostgreSQL)
    instead of the synchronous TriggerStore (SQLite).
    """

    def __init__(self, repository: TriggerRepository):
        """Initialize with a trigger repository.

        Args:
            repository: TriggerRepository instance (already user-scoped)
        """
        self._repo = repository

    async def create_trigger(
        self,
        *,
        agent_name: str,
        payload: str,
        recurrence_rule: Optional[str] = None,
        start_time: Optional[str] = None,
        timezone_name: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Trigger:
        """Create a new trigger.

        Args:
            agent_name: Name of the agent to trigger
            payload: Task payload
            recurrence_rule: Optional RRULE for recurring triggers
            start_time: Optional start time (ISO format or None for now)
            timezone_name: Optional timezone name
            status: Optional status override

        Returns:
            The created Trigger
        """
        tz = resolve_timezone(timezone_name)
        now = utc_now()
        start_dt_local = coerce_start_datetime(start_time, tz, now)
        stored_recurrence = build_recurrence(recurrence_rule, start_dt_local, tz)
        next_fire = self._compute_next_fire(
            stored_recurrence=stored_recurrence,
            start_dt_local=start_dt_local,
            tz=tz,
            now=now,
        )

        trigger = await self._repo.create_trigger(
            agent_name=agent_name,
            payload=payload,
            start_time=start_dt_local,
            next_trigger=next_fire,
            recurrence_rule=stored_recurrence,
            timezone=getattr(tz, "key", "UTC"),
            status=normalize_status(status),
            last_error=None,
        )
        return trigger

    async def update_trigger(
        self,
        trigger_id: int,
        *,
        agent_name: str,
        payload: Optional[str] = None,
        recurrence_rule: Optional[str] = None,
        start_time: Optional[str] = None,
        timezone_name: Optional[str] = None,
        status: Optional[str] = None,
        last_error: Optional[str] = None,
        clear_error: bool = False,
    ) -> Optional[Trigger]:
        """Update an existing trigger.

        Args:
            trigger_id: The trigger ID
            agent_name: The agent name (for validation)
            payload: New payload (optional)
            recurrence_rule: New recurrence rule (optional)
            start_time: New start time (optional)
            timezone_name: New timezone (optional)
            status: New status (optional)
            last_error: Error message to set (optional)
            clear_error: Whether to clear existing error

        Returns:
            The updated Trigger or None if not found
        """
        existing = await self._repo.get_one(trigger_id, agent_name)
        if existing is None:
            return None

        tz = resolve_timezone(timezone_name or existing.timezone)
        start_reference = existing.start_time if existing.start_time else utc_now()
        start_dt_local = coerce_start_datetime(start_time, tz, start_reference)

        fields: Dict[str, Any] = {}
        if payload is not None:
            fields["payload"] = payload

        normalized_status = None
        status_changed_to_active = False
        if status is not None:
            normalized_status = normalize_status(status)
            fields["status"] = normalized_status
            status_changed_to_active = (
                normalized_status == "active" and existing.status != "active"
            )
        else:
            normalized_status = existing.status

        if start_time is not None:
            fields["start_time"] = start_dt_local.astimezone(tz)
        if timezone_name is not None:
            fields["timezone"] = getattr(tz, "key", "UTC")

        schedule_inputs_changed = any(
            value is not None for value in (recurrence_rule, start_time, timezone_name)
        )

        recurrence_source = (
            recurrence_rule if recurrence_rule is not None else existing.recurrence_rule
        )
        if schedule_inputs_changed:
            stored_recurrence = (
                build_recurrence(recurrence_source, start_dt_local, tz)
                if recurrence_source
                else None
            )
        else:
            stored_recurrence = recurrence_source

        next_trigger_dt = existing.next_trigger
        now = utc_now()
        should_recompute_schedule = schedule_inputs_changed

        if status_changed_to_active:
            if next_trigger_dt is None:
                should_recompute_schedule = True
            else:
                missed_duration = now - next_trigger_dt
                if missed_duration > MISSED_TRIGGER_GRACE_PERIOD:
                    should_recompute_schedule = True

        if should_recompute_schedule:
            next_fire = self._compute_next_fire(
                stored_recurrence=stored_recurrence,
                start_dt_local=start_dt_local,
                tz=tz,
                now=now,
            )
            if (
                stored_recurrence is None
                and recurrence_rule is None
                and start_time is None
                and status_changed_to_active
                and next_fire is not None
                and next_fire <= now
            ):
                next_fire = now
            fields["next_trigger"] = next_fire
            if schedule_inputs_changed:
                fields["recurrence_rule"] = stored_recurrence
        elif schedule_inputs_changed:
            fields["recurrence_rule"] = stored_recurrence

        if clear_error:
            fields["last_error"] = None
        elif last_error is not None:
            fields["last_error"] = last_error

        if not fields:
            return existing

        await self._repo.update_trigger(trigger_id, agent_name, fields)
        return await self._repo.get_one(trigger_id, agent_name)

    async def list_triggers(self, *, agent_name: str) -> Sequence[Trigger]:
        """List all triggers for an agent.

        Args:
            agent_name: The agent name

        Returns:
            List of Triggers
        """
        return await self._repo.get_by_agent_name(agent_name)

    async def get_due_triggers(
        self, *, before: datetime, agent_name: Optional[str] = None
    ) -> Sequence[Trigger]:
        """Get triggers that are due to run.

        Args:
            before: Get triggers with next_trigger before this time
            agent_name: Optional filter by agent name

        Returns:
            List of due Triggers
        """
        return await self._repo.get_due_triggers(before, agent_name)

    async def mark_as_completed(self, trigger_id: int, *, agent_name: str) -> None:
        """Mark a trigger as completed.

        Args:
            trigger_id: The trigger ID
            agent_name: The agent name
        """
        await self._repo.mark_completed(trigger_id, agent_name)

    async def schedule_next_occurrence(
        self,
        trigger: Trigger,
        *,
        fired_at: datetime,
    ) -> Optional[Trigger]:
        """Schedule the next occurrence of a recurring trigger.

        Args:
            trigger: The trigger that just fired
            fired_at: When the trigger fired

        Returns:
            The updated Trigger
        """
        if not trigger.recurrence_rule:
            await self.mark_as_completed(trigger.id, agent_name=trigger.agent_name)
            return await self._repo.get_one(trigger.id, trigger.agent_name)

        tz = resolve_timezone(trigger.timezone)
        next_fire = self._compute_next_after(trigger.recurrence_rule, fired_at, tz)

        fields: Dict[str, Any] = {
            "next_trigger": next_fire,
            "last_error": None,
        }
        if next_fire is None:
            fields["status"] = "completed"

        await self._repo.update_trigger(trigger.id, trigger.agent_name, fields)
        return await self._repo.get_one(trigger.id, trigger.agent_name)

    async def record_failure(self, trigger: Trigger, error: str) -> None:
        """Record a failure on a trigger.

        Args:
            trigger: The trigger that failed
            error: The error message
        """
        await self._repo.set_error(trigger.id, trigger.agent_name, error)

    async def clear_next_fire(
        self, trigger_id: int, *, agent_name: str
    ) -> Optional[Trigger]:
        """Clear the next fire time for a trigger.

        Args:
            trigger_id: The trigger ID
            agent_name: The agent name

        Returns:
            The updated Trigger or None if not found
        """
        await self._repo.update_trigger(
            trigger_id, agent_name, {"next_trigger": None}
        )
        return await self._repo.get_one(trigger_id, agent_name)

    async def clear_all(self) -> None:
        """Clear all triggers for the current user."""
        await self._repo.clear_all()

    def _compute_next_fire(
        self,
        *,
        stored_recurrence: Optional[str],
        start_dt_local: datetime,
        tz: ZoneInfo,
        now: datetime,
    ) -> Optional[datetime]:
        """Compute the next fire time for a trigger.

        Args:
            stored_recurrence: The recurrence rule (RRULE string)
            start_dt_local: The start time in local timezone
            tz: The timezone
            now: Current UTC time

        Returns:
            Next fire time or None
        """
        if stored_recurrence:
            rule = load_rrule(stored_recurrence)
            next_occurrence = rule.after(now.astimezone(tz), inc=True)
            if next_occurrence is None:
                return None
            if next_occurrence.tzinfo is None:
                next_occurrence = next_occurrence.replace(tzinfo=tz)
            return next_occurrence.astimezone(tz)

        if start_dt_local < now.astimezone(tz):
            logger.warning(
                "start_time in the past; trigger will fire immediately",
                extra={"start_time": start_dt_local.isoformat()},
            )
        return start_dt_local

    def _compute_next_after(
        self,
        stored_recurrence: str,
        fired_at: datetime,
        tz: ZoneInfo,
    ) -> Optional[datetime]:
        """Compute the next occurrence after a fire.

        Args:
            stored_recurrence: The recurrence rule
            fired_at: When the trigger fired
            tz: The timezone

        Returns:
            Next occurrence or None if rule exhausted
        """
        rule = load_rrule(stored_recurrence)
        next_occurrence = rule.after(fired_at.astimezone(tz), inc=False)
        if next_occurrence is None:
            return None
        if next_occurrence.tzinfo is None:
            next_occurrence = next_occurrence.replace(tzinfo=tz)
        return next_occurrence.astimezone(tz)


__all__ = ["TriggerService", "MISSED_TRIGGER_GRACE_PERIOD"]
