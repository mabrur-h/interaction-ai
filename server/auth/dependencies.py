"""FastAPI authentication dependencies."""

import uuid
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.auth.jwt import verify_token
from server.database import User
from server.database.session import get_async_session

# HTTP Bearer token scheme
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    session: AsyncSession = Depends(get_async_session),
) -> User:
    """Get the current authenticated user.

    This dependency extracts and validates the JWT token from the Authorization header,
    then fetches the corresponding user from the database.

    Args:
        credentials: The HTTP Authorization credentials
        session: Database session

    Returns:
        The authenticated User object

    Raises:
        HTTPException: If authentication fails
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify the token
    token_payload = verify_token(credentials.credentials, expected_type="access")
    if token_payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    try:
        user_id = uuid.UUID(token_payload.sub)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    session: AsyncSession = Depends(get_async_session),
) -> Optional[User]:
    """Get the current user if authenticated, None otherwise.

    This is useful for endpoints that work both with and without authentication,
    providing different functionality based on auth status.

    Args:
        credentials: The HTTP Authorization credentials
        session: Database session

    Returns:
        The authenticated User object, or None if not authenticated
    """
    if credentials is None:
        return None

    # Verify the token
    token_payload = verify_token(credentials.credentials, expected_type="access")
    if token_payload is None:
        return None

    # Get user from database
    try:
        user_id = uuid.UUID(token_payload.sub)
    except ValueError:
        return None

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        return None

    return user
