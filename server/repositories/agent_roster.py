"""Agent roster repository."""

import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from server.database.models import AgentRoster
from server.repositories.base import UserScopedRepository


class AgentRosterRepository(UserScopedRepository[AgentRoster]):
    """Repository for agent roster operations (user-scoped)."""

    model = AgentRoster

    async def get_agent_names(self) -> Sequence[str]:
        """Get all registered agent names for the user.

        Returns:
            List of agent names
        """
        result = await self.session.execute(
            select(AgentRoster.agent_name)
            .where(AgentRoster.user_id == self.user_id)
            .order_by(AgentRoster.created_at)
        )
        return [row[0] for row in result.fetchall()]

    async def has_agent(self, agent_name: str) -> bool:
        """Check if an agent is registered.

        Args:
            agent_name: The agent name

        Returns:
            True if registered, False otherwise
        """
        result = await self.session.execute(
            select(AgentRoster.id).where(
                AgentRoster.user_id == self.user_id,
                AgentRoster.agent_name == agent_name,
            )
        )
        return result.scalar_one_or_none() is not None

    async def register_agent(self, agent_name: str) -> AgentRoster:
        """Register a new agent.

        Uses upsert to handle duplicates gracefully.

        Args:
            agent_name: The agent name

        Returns:
            The AgentRoster record
        """
        stmt = insert(AgentRoster).values(
            user_id=self.user_id,
            agent_name=agent_name,
        ).on_conflict_do_nothing(
            index_elements=["user_id", "agent_name"]
        )
        await self.session.execute(stmt)
        await self.session.flush()

        # Get the record
        result = await self.session.execute(
            select(AgentRoster).where(
                AgentRoster.user_id == self.user_id,
                AgentRoster.agent_name == agent_name,
            )
        )
        return result.scalar_one()

    async def unregister_agent(self, agent_name: str) -> bool:
        """Unregister an agent.

        Args:
            agent_name: The agent name

        Returns:
            True if removed, False if not found
        """
        result = await self.session.execute(
            select(AgentRoster).where(
                AgentRoster.user_id == self.user_id,
                AgentRoster.agent_name == agent_name,
            )
        )
        agent = result.scalar_one_or_none()

        if agent is None:
            return False

        return await self.delete(agent.id)
