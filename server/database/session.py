"""Async database session management."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from server.database.config import (
    get_database_url,
    DATABASE_POOL_SIZE,
    DATABASE_MAX_OVERFLOW,
    DATABASE_POOL_TIMEOUT,
    DATABASE_ECHO,
)

# Create async engine
engine = create_async_engine(
    get_database_url(),
    pool_size=DATABASE_POOL_SIZE,
    max_overflow=DATABASE_MAX_OVERFLOW,
    pool_timeout=DATABASE_POOL_TIMEOUT,
    pool_pre_ping=True,  # Verify connections before use
    echo=DATABASE_ECHO,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async database session.

    Usage:
        @router.get("/users")
        async def get_users(session: AsyncSession = Depends(get_async_session)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def async_session_factory() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for async database sessions.

    Use this in Celery tasks or other non-FastAPI contexts where
    you need a database session.

    Usage:
        async with async_session_factory() as session:
            repo = UserRepository(session)
            users = await repo.get_all()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize the database (create tables if they don't exist).

    Note: In production, use Alembic migrations instead.
    """
    from server.database.models import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()
