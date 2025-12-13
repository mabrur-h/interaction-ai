"""Async execution agent log service using PostgreSQL repository."""

from __future__ import annotations

from html import escape
from typing import List, Sequence, Tuple

from server.database.models import ExecutionLog
from server.repositories.execution_logs import ExecutionLogRepository


class ExecutionLogService:
    """Async execution agent log management.

    This is the v2 version that uses ExecutionLogRepository (PostgreSQL)
    instead of file-based storage.
    """

    def __init__(self, repo: ExecutionLogRepository):
        """Initialize with execution log repository.

        Args:
            repo: ExecutionLogRepository instance (user-scoped)
        """
        self._repo = repo

    async def record_request(self, agent_name: str, instructions: str) -> ExecutionLog:
        """Record an incoming request from the interaction agent.

        Args:
            agent_name: Name of the agent
            instructions: Request instructions

        Returns:
            The created ExecutionLog
        """
        return await self._repo.add_request_log(agent_name, instructions)

    async def record_action(self, agent_name: str, description: str) -> ExecutionLog:
        """Record an agent action (tool call).

        Args:
            agent_name: Name of the agent
            description: Action description

        Returns:
            The created ExecutionLog
        """
        return await self._repo.add_action_log(agent_name, description)

    async def record_tool_response(
        self, agent_name: str, tool_name: str, response: str
    ) -> ExecutionLog:
        """Record the response from a tool.

        Args:
            agent_name: Name of the agent
            tool_name: Name of the tool
            response: Tool response

        Returns:
            The created ExecutionLog
        """
        content = f"{tool_name}: {response}"
        return await self._repo.add_tool_response_log(agent_name, content)

    async def record_agent_response(self, agent_name: str, response: str) -> ExecutionLog:
        """Record the agent's final response.

        Args:
            agent_name: Name of the agent
            response: Agent response

        Returns:
            The created ExecutionLog
        """
        return await self._repo.add_response_log(agent_name, response)

    async def get_entries(
        self, agent_name: str, limit: int = 100
    ) -> List[Tuple[str, str, str]]:
        """Get log entries for an agent.

        Args:
            agent_name: Name of the agent
            limit: Maximum number of entries

        Returns:
            List of (tag, timestamp, content) tuples
        """
        logs = await self._repo.get_logs_for_agent(agent_name, limit)
        # Reverse to get chronological order (oldest first)
        logs = list(reversed(logs))
        return [
            (log.tag, log.created_at.strftime("%Y-%m-%d %H:%M:%S"), log.content)
            for log in logs
        ]

    async def load_transcript(self, agent_name: str, limit: int = 100) -> str:
        """Load the full transcript for inclusion in system prompt.

        Args:
            agent_name: Name of the agent
            limit: Maximum number of entries

        Returns:
            Formatted transcript string in XML-style format
        """
        entries = await self.get_entries(agent_name, limit)
        parts: List[str] = []
        for tag, timestamp, content in entries:
            escaped = escape(content, quote=False)
            if timestamp:
                parts.append(f"<{tag} timestamp=\"{timestamp}\">{escaped}</{tag}>")
            else:
                parts.append(f"<{tag}>{escaped}</{tag}>")
        return "\n".join(parts)

    async def load_recent(
        self, agent_name: str, limit: int = 10
    ) -> List[Tuple[str, str, str]]:
        """Load recent log entries.

        Args:
            agent_name: Name of the agent
            limit: Maximum number of entries

        Returns:
            List of (tag, timestamp, content) tuples
        """
        logs = await self._repo.get_logs_for_agent(agent_name, limit)
        # Reverse to get chronological order
        logs = list(reversed(logs))
        return [
            (log.tag, log.created_at.strftime("%Y-%m-%d %H:%M:%S"), log.content)
            for log in logs
        ]

    async def get_transcript(self, agent_name: str, limit: int = 50) -> str:
        """Get a simple formatted transcript.

        Args:
            agent_name: Name of the agent
            limit: Maximum number of entries

        Returns:
            Simple formatted transcript
        """
        return await self._repo.get_transcript(agent_name, limit)


__all__ = ["ExecutionLogService"]
