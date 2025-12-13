"""OAuth connections repository."""

import uuid
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from server.database.models import OAuthConnection
from server.repositories.base import UserScopedRepository


class OAuthConnectionRepository(UserScopedRepository[OAuthConnection]):
    """Repository for OAuth connection operations (user-scoped)."""

    model = OAuthConnection

    async def get_by_provider(self, provider: str) -> Optional[OAuthConnection]:
        """Get connection for a specific provider.

        Args:
            provider: Provider name ('gmail', 'calendar')

        Returns:
            The OAuthConnection or None
        """
        result = await self.session.execute(
            select(OAuthConnection).where(
                OAuthConnection.user_id == self.user_id,
                OAuthConnection.provider == provider,
            )
        )
        return result.scalar_one_or_none()

    async def get_gmail_connection(self) -> Optional[OAuthConnection]:
        """Get the Gmail connection.

        Returns:
            The Gmail OAuthConnection or None
        """
        return await self.get_by_provider("gmail")

    async def get_calendar_connection(self) -> Optional[OAuthConnection]:
        """Get the Calendar connection.

        Returns:
            The Calendar OAuthConnection or None
        """
        return await self.get_by_provider("calendar")

    async def upsert_connection(
        self,
        provider: str,
        composio_user_id: str,
        composio_connection_id: Optional[str] = None,
        provider_email: Optional[str] = None,
        status: str = "pending",
        extra_data: Optional[dict] = None,
    ) -> OAuthConnection:
        """Create or update an OAuth connection.

        Args:
            provider: Provider name
            composio_user_id: Composio user ID
            composio_connection_id: Composio connection ID
            provider_email: Email from the provider
            status: Connection status
            extra_data: Additional extra data

        Returns:
            The OAuthConnection
        """
        stmt = insert(OAuthConnection).values(
            user_id=self.user_id,
            provider=provider,
            composio_user_id=composio_user_id,
            composio_connection_id=composio_connection_id,
            provider_email=provider_email,
            status=status,
            extra_data=extra_data or {},
        ).on_conflict_do_update(
            index_elements=["user_id", "provider"],
            set_={
                "composio_user_id": composio_user_id,
                "composio_connection_id": composio_connection_id,
                "provider_email": provider_email,
                "status": status,
                "extra_data": extra_data or {},
            },
        )
        await self.session.execute(stmt)
        await self.session.flush()

        return await self.get_by_provider(provider)

    async def update_status(
        self,
        provider: str,
        status: str,
        provider_email: Optional[str] = None,
        composio_connection_id: Optional[str] = None,
    ) -> Optional[OAuthConnection]:
        """Update connection status.

        Args:
            provider: Provider name
            status: New status
            provider_email: Optional email to update
            composio_connection_id: Optional connection ID to update

        Returns:
            The updated OAuthConnection or None
        """
        conn = await self.get_by_provider(provider)
        if conn is None:
            return None

        updates = {"status": status}
        if provider_email is not None:
            updates["provider_email"] = provider_email
        if composio_connection_id is not None:
            updates["composio_connection_id"] = composio_connection_id

        return await self.update(conn.id, **updates)

    async def disconnect(self, provider: str) -> bool:
        """Disconnect/delete a provider connection.

        Args:
            provider: Provider name

        Returns:
            True if deleted, False if not found
        """
        conn = await self.get_by_provider(provider)
        if conn is None:
            return False
        return await self.delete(conn.id)

    async def get_active_connections(self) -> Sequence[OAuthConnection]:
        """Get all active connections for the user.

        Returns:
            List of active OAuthConnections
        """
        result = await self.session.execute(
            select(OAuthConnection).where(
                OAuthConnection.user_id == self.user_id,
                OAuthConnection.status == "active",
            )
        )
        return result.scalars().all()
