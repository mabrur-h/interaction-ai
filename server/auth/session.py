"""Session management with Redis backing."""

import hashlib
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

import redis.asyncio as redis
from pydantic import BaseModel

from server.config import get_settings

logger = logging.getLogger(__name__)


class SessionData(BaseModel):
    """Session data stored in Redis."""

    user_id: str
    refresh_token_hash: str
    expires_at: datetime
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime


# Redis client singleton
_redis_client: Optional[redis.Redis] = None


async def get_redis_client() -> redis.Redis:
    """Get the Redis client singleton."""
    global _redis_client
    if _redis_client is None:
        settings = get_settings()
        _redis_client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


async def close_redis() -> None:
    """Close the Redis connection."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None


def hash_token(token: str) -> str:
    """Create a SHA-256 hash of a token for secure storage."""
    return hashlib.sha256(token.encode()).hexdigest()


async def create_session(
    user_id: uuid.UUID,
    refresh_token: str,
    expires_at: datetime,
    user_agent: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> str:
    """Create a new session in Redis.

    Args:
        user_id: The user's UUID
        refresh_token: The refresh token to store
        expires_at: When the session expires
        user_agent: Optional user agent string
        ip_address: Optional IP address

    Returns:
        The session ID
    """
    client = await get_redis_client()
    session_id = str(uuid.uuid4())
    token_hash = hash_token(refresh_token)

    session_data = SessionData(
        user_id=str(user_id),
        refresh_token_hash=token_hash,
        expires_at=expires_at,
        user_agent=user_agent,
        ip_address=ip_address,
        created_at=datetime.now(timezone.utc),
    )

    # Calculate TTL in seconds
    ttl = int((expires_at - datetime.now(timezone.utc)).total_seconds())
    if ttl <= 0:
        ttl = 1  # Minimum TTL

    # Store session data
    key = f"session:{session_id}"
    await client.setex(key, ttl, session_data.model_dump_json())

    # Also store a reverse mapping from token hash to session ID
    # This allows us to find and invalidate sessions by token
    token_key = f"token:{token_hash}"
    await client.setex(token_key, ttl, session_id)

    # Store user's sessions list for "logout all" functionality
    user_sessions_key = f"user_sessions:{user_id}"
    await client.sadd(user_sessions_key, session_id)
    await client.expire(user_sessions_key, ttl)

    logger.debug(f"Created session {session_id} for user {user_id}")
    return session_id


async def get_session(session_id: str) -> Optional[SessionData]:
    """Get session data by session ID.

    Args:
        session_id: The session ID

    Returns:
        SessionData if found, None otherwise
    """
    client = await get_redis_client()
    key = f"session:{session_id}"
    data = await client.get(key)

    if data is None:
        return None

    return SessionData.model_validate_json(data)


async def get_session_by_token(refresh_token: str) -> Optional[tuple[str, SessionData]]:
    """Get session data by refresh token.

    Args:
        refresh_token: The refresh token

    Returns:
        Tuple of (session_id, SessionData) if found, None otherwise
    """
    client = await get_redis_client()
    token_hash = hash_token(refresh_token)
    token_key = f"token:{token_hash}"

    session_id = await client.get(token_key)
    if session_id is None:
        return None

    session_data = await get_session(session_id)
    if session_data is None:
        return None

    # Verify token hash matches
    if session_data.refresh_token_hash != token_hash:
        return None

    return session_id, session_data


async def delete_session(session_id: str) -> bool:
    """Delete a session.

    Args:
        session_id: The session ID to delete

    Returns:
        True if deleted, False if not found
    """
    client = await get_redis_client()

    # Get session data first to clean up related keys
    session_data = await get_session(session_id)
    if session_data is None:
        return False

    # Delete session
    key = f"session:{session_id}"
    await client.delete(key)

    # Delete token mapping
    token_key = f"token:{session_data.refresh_token_hash}"
    await client.delete(token_key)

    # Remove from user's sessions set
    user_sessions_key = f"user_sessions:{session_data.user_id}"
    await client.srem(user_sessions_key, session_id)

    logger.debug(f"Deleted session {session_id}")
    return True


async def delete_session_by_token(refresh_token: str) -> bool:
    """Delete a session by refresh token.

    Args:
        refresh_token: The refresh token

    Returns:
        True if deleted, False if not found
    """
    result = await get_session_by_token(refresh_token)
    if result is None:
        return False

    session_id, _ = result
    return await delete_session(session_id)


async def delete_all_user_sessions(user_id: uuid.UUID) -> int:
    """Delete all sessions for a user (logout everywhere).

    Args:
        user_id: The user's UUID

    Returns:
        Number of sessions deleted
    """
    client = await get_redis_client()
    user_sessions_key = f"user_sessions:{user_id}"

    # Get all session IDs for this user
    session_ids = await client.smembers(user_sessions_key)
    if not session_ids:
        return 0

    count = 0
    for session_id in session_ids:
        if await delete_session(session_id):
            count += 1

    # Clean up the user sessions set
    await client.delete(user_sessions_key)

    logger.info(f"Deleted {count} sessions for user {user_id}")
    return count


async def is_token_valid(refresh_token: str) -> bool:
    """Check if a refresh token is still valid (not revoked).

    Args:
        refresh_token: The refresh token to check

    Returns:
        True if valid, False if revoked or expired
    """
    result = await get_session_by_token(refresh_token)
    return result is not None
