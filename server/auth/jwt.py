"""JWT token creation and validation."""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import JWTError, jwt
from pydantic import BaseModel

from server.config import get_settings


class TokenPayload(BaseModel):
    """JWT token payload."""

    sub: str  # Subject (user_id)
    exp: datetime  # Expiration time
    iat: datetime  # Issued at
    type: str  # Token type: 'access' or 'refresh'
    jti: Optional[str] = None  # JWT ID (for refresh tokens)


class TokenPair(BaseModel):
    """Access and refresh token pair."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # Access token expiration in seconds


def create_access_token(
    user_id: uuid.UUID,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a new access token.

    Args:
        user_id: The user's UUID
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT access token
    """
    settings = get_settings()

    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.jwt_access_token_expire_minutes)

    now = datetime.now(timezone.utc)
    expire = now + expires_delta

    payload = {
        "sub": str(user_id),
        "exp": expire,
        "iat": now,
        "type": "access",
    }

    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(
    user_id: uuid.UUID,
    expires_delta: Optional[timedelta] = None,
) -> tuple[str, str, datetime]:
    """Create a new refresh token.

    Args:
        user_id: The user's UUID
        expires_delta: Optional custom expiration time

    Returns:
        Tuple of (encoded JWT, token ID, expiration datetime)
    """
    settings = get_settings()

    if expires_delta is None:
        expires_delta = timedelta(days=settings.jwt_refresh_token_expire_days)

    now = datetime.now(timezone.utc)
    expire = now + expires_delta
    token_id = str(uuid.uuid4())

    payload = {
        "sub": str(user_id),
        "exp": expire,
        "iat": now,
        "type": "refresh",
        "jti": token_id,
    }

    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, token_id, expire


def verify_token(token: str, expected_type: str = "access") -> Optional[TokenPayload]:
    """Verify and decode a JWT token.

    Args:
        token: The JWT token string
        expected_type: Expected token type ('access' or 'refresh')

    Returns:
        TokenPayload if valid, None otherwise
    """
    settings = get_settings()

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        # Verify token type
        if payload.get("type") != expected_type:
            return None

        return TokenPayload(
            sub=payload["sub"],
            exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
            iat=datetime.fromtimestamp(payload["iat"], tz=timezone.utc),
            type=payload["type"],
            jti=payload.get("jti"),
        )
    except JWTError:
        return None


def create_token_pair(user_id: uuid.UUID) -> tuple[TokenPair, str, datetime]:
    """Create a complete token pair (access + refresh).

    Args:
        user_id: The user's UUID

    Returns:
        Tuple of (TokenPair, refresh_token_id, refresh_expiration)
    """
    settings = get_settings()

    access_token = create_access_token(user_id)
    refresh_token, token_id, expire = create_refresh_token(user_id)

    token_pair = TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )

    return token_pair, token_id, expire
