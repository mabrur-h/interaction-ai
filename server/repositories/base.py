"""Base repository class with common functionality."""

import uuid
from typing import Generic, Optional, Sequence, Type, TypeVar

from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from server.database.models import Base

# Generic type for SQLAlchemy models
ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """Base repository providing common CRUD operations.

    All repositories inherit from this class and can override methods
    as needed for custom functionality.
    """

    model: Type[ModelT]

    def __init__(self, session: AsyncSession):
        """Initialize with a database session.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def get_by_id(self, id: uuid.UUID | int) -> Optional[ModelT]:
        """Get a single record by ID.

        Args:
            id: The primary key ID

        Returns:
            The model instance or None if not found
        """
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(self, limit: int = 100, offset: int = 0) -> Sequence[ModelT]:
        """Get all records with pagination.

        Args:
            limit: Maximum number of records
            offset: Number of records to skip

        Returns:
            List of model instances
        """
        result = await self.session.execute(
            select(self.model).limit(limit).offset(offset)
        )
        return result.scalars().all()

    async def create(self, **kwargs) -> ModelT:
        """Create a new record.

        Args:
            **kwargs: Field values for the new record

        Returns:
            The created model instance
        """
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def update(self, id: uuid.UUID | int, **kwargs) -> Optional[ModelT]:
        """Update a record by ID.

        Args:
            id: The primary key ID
            **kwargs: Field values to update

        Returns:
            The updated model instance or None if not found
        """
        await self.session.execute(
            update(self.model).where(self.model.id == id).values(**kwargs)
        )
        return await self.get_by_id(id)

    async def delete(self, id: uuid.UUID | int) -> bool:
        """Delete a record by ID.

        Args:
            id: The primary key ID

        Returns:
            True if deleted, False if not found
        """
        result = await self.session.execute(
            delete(self.model).where(self.model.id == id)
        )
        return result.rowcount > 0

    async def exists(self, id: uuid.UUID | int) -> bool:
        """Check if a record exists.

        Args:
            id: The primary key ID

        Returns:
            True if exists, False otherwise
        """
        result = await self.session.execute(
            select(self.model.id).where(self.model.id == id)
        )
        return result.scalar_one_or_none() is not None


class UserScopedRepository(BaseRepository[ModelT]):
    """Repository with automatic user_id filtering.

    Use this for models that have a user_id foreign key.
    All queries are automatically scoped to the current user.
    """

    def __init__(self, session: AsyncSession, user_id: uuid.UUID):
        """Initialize with a database session and user ID.

        Args:
            session: SQLAlchemy async session
            user_id: The current user's UUID
        """
        super().__init__(session)
        self.user_id = user_id

    async def get_by_id(self, id: uuid.UUID | int) -> Optional[ModelT]:
        """Get a record by ID, scoped to the current user.

        Args:
            id: The primary key ID

        Returns:
            The model instance or None if not found
        """
        result = await self.session.execute(
            select(self.model).where(
                self.model.id == id,
                self.model.user_id == self.user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_all(self, limit: int = 100, offset: int = 0) -> Sequence[ModelT]:
        """Get all records for the current user.

        Args:
            limit: Maximum number of records
            offset: Number of records to skip

        Returns:
            List of model instances
        """
        result = await self.session.execute(
            select(self.model)
            .where(self.model.user_id == self.user_id)
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def create(self, **kwargs) -> ModelT:
        """Create a new record for the current user.

        Args:
            **kwargs: Field values for the new record

        Returns:
            The created model instance
        """
        kwargs["user_id"] = self.user_id
        return await super().create(**kwargs)

    async def update(self, id: uuid.UUID | int, **kwargs) -> Optional[ModelT]:
        """Update a record, scoped to the current user.

        Args:
            id: The primary key ID
            **kwargs: Field values to update

        Returns:
            The updated model instance or None if not found
        """
        await self.session.execute(
            update(self.model)
            .where(
                self.model.id == id,
                self.model.user_id == self.user_id,
            )
            .values(**kwargs)
        )
        return await self.get_by_id(id)

    async def delete(self, id: uuid.UUID | int) -> bool:
        """Delete a record, scoped to the current user.

        Args:
            id: The primary key ID

        Returns:
            True if deleted, False if not found
        """
        result = await self.session.execute(
            delete(self.model).where(
                self.model.id == id,
                self.model.user_id == self.user_id,
            )
        )
        return result.rowcount > 0
