"""Database configuration."""

import os
from functools import lru_cache


@lru_cache(maxsize=1)
def get_database_url() -> str:
    """Get the database URL from environment variables.

    Railway provides DATABASE_URL automatically for managed PostgreSQL.
    For local development, use docker-compose defaults.
    """
    url = os.getenv("DATABASE_URL")

    if url:
        # Railway provides postgres:// but SQLAlchemy needs postgresql://
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://") and "+asyncpg" not in url:
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    # Local development defaults (matches docker-compose.yml)
    return "postgresql+asyncpg://openpoke:openpoke_dev_password@localhost:5432/openpoke"


@lru_cache(maxsize=1)
def get_redis_url() -> str:
    """Get the Redis URL from environment variables.

    Railway provides REDIS_URL automatically for managed Redis.
    For local development, use docker-compose defaults.
    """
    return os.getenv("REDIS_URL", "redis://localhost:6379/0")


# Database settings
DATABASE_POOL_SIZE = int(os.getenv("DATABASE_POOL_SIZE", "5"))
DATABASE_MAX_OVERFLOW = int(os.getenv("DATABASE_MAX_OVERFLOW", "10"))
DATABASE_POOL_TIMEOUT = int(os.getenv("DATABASE_POOL_TIMEOUT", "30"))
DATABASE_ECHO = os.getenv("DATABASE_ECHO", "0") == "1"
