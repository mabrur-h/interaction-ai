"""Family relationship repository for Wally Junior."""

import uuid
from typing import Optional, Sequence

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from server.database.models import FamilyRelationship, User
from server.repositories.base import BaseRepository


class FamilyRepository(BaseRepository[FamilyRelationship]):
    """Repository for FamilyRelationship operations.

    Note: This repository is NOT user-scoped because relationships
    involve two users. Operations should specify parent or child explicitly.
    """

    model = FamilyRelationship

    def __init__(self, session: AsyncSession, user_id: uuid.UUID):
        """Initialize with a database session and user ID.

        Args:
            session: SQLAlchemy async session
            user_id: The current user's UUID (can be parent or child)
        """
        super().__init__(session)
        self.user_id = user_id

    async def link_child(
        self,
        child_id: uuid.UUID,
        relationship_type: str = "parent",
    ) -> FamilyRelationship:
        """Link a child to the current user (as parent).

        Args:
            child_id: The child's user ID
            relationship_type: Type of relationship (default: parent)

        Returns:
            The created FamilyRelationship
        """
        return await self.create(
            parent_id=self.user_id,
            child_id=child_id,
            relationship_type=relationship_type,
        )

    async def get_children(self) -> Sequence[User]:
        """Get all children linked to the current user (as parent).

        Returns:
            List of child User objects
        """
        result = await self.session.execute(
            select(User)
            .join(FamilyRelationship, FamilyRelationship.child_id == User.id)
            .where(FamilyRelationship.parent_id == self.user_id)
            .order_by(User.display_name)
        )
        return result.scalars().all()

    async def get_parents(self) -> Sequence[User]:
        """Get all parents linked to the current user (as child).

        Returns:
            List of parent User objects
        """
        result = await self.session.execute(
            select(User)
            .join(FamilyRelationship, FamilyRelationship.parent_id == User.id)
            .where(FamilyRelationship.child_id == self.user_id)
            .order_by(User.display_name)
        )
        return result.scalars().all()

    async def is_parent_of(self, child_id: uuid.UUID) -> bool:
        """Check if current user is a parent of the given child.

        Args:
            child_id: The child's user ID

        Returns:
            True if current user is parent of child
        """
        result = await self.session.execute(
            select(FamilyRelationship.id).where(
                FamilyRelationship.parent_id == self.user_id,
                FamilyRelationship.child_id == child_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def is_child_of(self, parent_id: uuid.UUID) -> bool:
        """Check if current user is a child of the given parent.

        Args:
            parent_id: The parent's user ID

        Returns:
            True if current user is child of parent
        """
        result = await self.session.execute(
            select(FamilyRelationship.id).where(
                FamilyRelationship.parent_id == parent_id,
                FamilyRelationship.child_id == self.user_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def unlink_child(self, child_id: uuid.UUID) -> bool:
        """Remove parent-child relationship.

        Args:
            child_id: The child's user ID

        Returns:
            True if relationship was deleted
        """
        result = await self.session.execute(
            select(FamilyRelationship).where(
                FamilyRelationship.parent_id == self.user_id,
                FamilyRelationship.child_id == child_id,
            )
        )
        relationship = result.scalar_one_or_none()
        if relationship:
            await self.session.delete(relationship)
            return True
        return False

    async def get_child_with_stats(self, child_id: uuid.UUID) -> Optional[dict]:
        """Get child user with their financial stats.

        Args:
            child_id: The child's user ID

        Returns:
            Dictionary with child info and stats, or None if not found
        """
        # First verify this is a child of current user
        if not await self.is_parent_of(child_id):
            return None

        result = await self.session.execute(
            select(User).where(User.id == child_id)
        )
        child = result.scalar_one_or_none()
        if not child:
            return None

        return {
            "id": str(child.id),
            "display_name": child.display_name,
            "email": child.email,
            "avatar_url": child.avatar_url,
            "initial_balance": child.initial_balance,
            "created_at": child.created_at,
        }
