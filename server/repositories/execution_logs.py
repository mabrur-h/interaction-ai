"""Execution logs repository."""

import uuid
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.database.models import ExecutionLog
from server.repositories.base import UserScopedRepository


class ExecutionLogRepository(UserScopedRepository[ExecutionLog]):
    """Repository for execution log operations (user-scoped)."""

    model = ExecutionLog

    async def get_logs_for_agent(
        self, agent_name: str, limit: int = 100
    ) -> Sequence[ExecutionLog]:
        """Get logs for a specific agent.

        Args:
            agent_name: The agent name
            limit: Maximum number of logs

        Returns:
            List of ExecutionLogs, most recent first
        """
        result = await self.session.execute(
            select(ExecutionLog)
            .where(
                ExecutionLog.user_id == self.user_id,
                ExecutionLog.agent_name == agent_name,
            )
            .order_by(ExecutionLog.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def add_log(
        self,
        agent_name: str,
        tag: str,
        content: str,
    ) -> ExecutionLog:
        """Add a new execution log entry.

        Args:
            agent_name: Name of the agent
            tag: Log tag ('agent_request', 'agent_action', 'tool_response', 'agent_response')
            content: Log content

        Returns:
            The created ExecutionLog
        """
        return await self.create(
            agent_name=agent_name,
            tag=tag,
            content=content,
        )

    async def add_request_log(self, agent_name: str, content: str) -> ExecutionLog:
        """Add an agent request log.

        Args:
            agent_name: Name of the agent
            content: Request content

        Returns:
            The created ExecutionLog
        """
        return await self.add_log(agent_name, "agent_request", content)

    async def add_action_log(self, agent_name: str, content: str) -> ExecutionLog:
        """Add an agent action log.

        Args:
            agent_name: Name of the agent
            content: Action content

        Returns:
            The created ExecutionLog
        """
        return await self.add_log(agent_name, "agent_action", content)

    async def add_tool_response_log(
        self, agent_name: str, content: str
    ) -> ExecutionLog:
        """Add a tool response log.

        Args:
            agent_name: Name of the agent
            content: Tool response content

        Returns:
            The created ExecutionLog
        """
        return await self.add_log(agent_name, "tool_response", content)

    async def add_response_log(self, agent_name: str, content: str) -> ExecutionLog:
        """Add an agent response log.

        Args:
            agent_name: Name of the agent
            content: Response content

        Returns:
            The created ExecutionLog
        """
        return await self.add_log(agent_name, "agent_response", content)

    async def get_transcript(self, agent_name: str, limit: int = 50) -> str:
        """Get a formatted transcript of agent logs.

        Args:
            agent_name: Name of the agent
            limit: Maximum number of log entries

        Returns:
            Formatted transcript string
        """
        logs = await self.get_logs_for_agent(agent_name, limit)
        # Reverse to get chronological order
        logs = list(reversed(logs))

        lines = []
        for log in logs:
            tag_labels = {
                "agent_request": "REQUEST",
                "agent_action": "ACTION",
                "tool_response": "TOOL",
                "agent_response": "RESPONSE",
            }
            label = tag_labels.get(log.tag, log.tag.upper())
            lines.append(f"[{label}] {log.content}")

        return "\n".join(lines)
