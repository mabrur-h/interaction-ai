"""User repository."""

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.database.models import User
from server.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User operations."""

    model = User

    async def get_by_google_id(self, google_id: str) -> Optional[User]:
        """Get a user by their Google ID.

        Args:
            google_id: Google's unique user ID

        Returns:
            The User or None if not found
        """
        result = await self.session.execute(
            select(User).where(User.google_id == google_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get a user by email.

        Args:
            email: User's email address

        Returns:
            The User or None if not found
        """
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def create_from_google(
        self,
        google_id: str,
        email: str,
        display_name: Optional[str] = None,
        avatar_url: Optional[str] = None,
    ) -> User:
        """Create a new user from Google OAuth.

        Args:
            google_id: Google's unique user ID
            email: User's email
            display_name: User's display name
            avatar_url: URL to user's avatar

        Returns:
            The created User
        """
        return await self.create(
            google_id=google_id,
            email=email,
            display_name=display_name,
            avatar_url=avatar_url,
        )

    async def update_timezone(self, user_id: uuid.UUID, timezone: str) -> Optional[User]:
        """Update user's timezone.

        Args:
            user_id: The user's UUID
            timezone: The new timezone

        Returns:
            The updated User or None if not found
        """
        return await self.update(user_id, timezone=timezone)
