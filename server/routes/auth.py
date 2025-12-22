"""Authentication routes."""

import logging
import secrets
import uuid
from datetime import datetime, timezone
from typing import Optional

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.auth.dependencies import get_current_user
from server.auth.google import GoogleOAuth, get_google_oauth
from server.auth.jwt import (
    TokenPair,
    create_token_pair,
    verify_token,
)
from server.auth.session import (
    create_session,
    delete_all_user_sessions,
    delete_session_by_token,
    is_token_valid,
)
from server.config import get_settings
from server.database import User
from server.database.models import InviteCode, FamilyRelationship
from server.database.session import get_async_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


# Request/Response models
class TokenRefreshRequest(BaseModel):
    """Request to refresh access token."""

    refresh_token: str


class TokenResponse(BaseModel):
    """Token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    """User information response."""

    id: str
    email: str
    display_name: Optional[str]
    avatar_url: Optional[str]
    timezone: str
    created_at: datetime
    user_type: str = "adult"
    initial_balance: int = 0

    class Config:
        from_attributes = True


class AuthStatusResponse(BaseModel):
    """Authentication status response."""

    authenticated: bool
    user: Optional[UserResponse] = None


# In-memory state storage for OAuth (in production, use Redis)
_oauth_states: dict[str, datetime] = {}


def _generate_state() -> str:
    """Generate and store a CSRF state token."""
    state = secrets.token_urlsafe(32)
    _oauth_states[state] = datetime.now(timezone.utc)
    # Clean up old states (older than 10 minutes)
    cutoff = datetime.now(timezone.utc).timestamp() - 600
    _oauth_states.clear()
    _oauth_states[state] = datetime.now(timezone.utc)
    return state


def _verify_state(state: str) -> bool:
    """Verify and consume a CSRF state token."""
    if state not in _oauth_states:
        return False
    created = _oauth_states.pop(state)
    # Check if state is not older than 10 minutes
    age = (datetime.now(timezone.utc) - created).total_seconds()
    return age < 600


@router.get("/google/login")
async def google_login() -> RedirectResponse:
    """Initiate Google OAuth login.

    Redirects the user to Google's OAuth consent screen.
    """
    settings = get_settings()

    if not settings.google_client_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth is not configured",
        )

    google = get_google_oauth()
    state = _generate_state()
    auth_url = google.get_authorization_url(state=state)

    return RedirectResponse(url=auth_url)


@router.get("/google/callback")
async def google_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    session: AsyncSession = Depends(get_async_session),
    request: Request = None,
) -> RedirectResponse:
    """Handle Google OAuth callback.

    This endpoint is called by Google after the user authorizes the app.
    It exchanges the authorization code for tokens and creates/updates the user.
    """
    settings = get_settings()

    # Handle OAuth errors
    if error:
        logger.warning(f"Google OAuth error: {error}")
        return RedirectResponse(
            url=f"{settings.frontend_url}/login?error={error}"
        )

    # Verify required parameters
    if not code:
        return RedirectResponse(
            url=f"{settings.frontend_url}/login?error=missing_code"
        )

    # Verify state (CSRF protection)
    if not state or not _verify_state(state):
        logger.warning("Invalid OAuth state")
        return RedirectResponse(
            url=f"{settings.frontend_url}/login?error=invalid_state"
        )

    try:
        # Exchange code for user info
        google = get_google_oauth()
        user_info = await google.authenticate(code)

        # Find or create user
        result = await session.execute(
            select(User).where(User.google_id == user_info.id)
        )
        user = result.scalar_one_or_none()

        if user is None:
            # Create new user
            user = User(
                google_id=user_info.id,
                email=user_info.email,
                display_name=user_info.name,
                avatar_url=user_info.picture,
            )
            session.add(user)
            await session.flush()
            logger.info(f"Created new user: {user.email}")
        else:
            # Update existing user
            user.email = user_info.email
            user.display_name = user_info.name
            user.avatar_url = user_info.picture
            user.last_login_at = datetime.now(timezone.utc)
            logger.info(f"User logged in: {user.email}")

        await session.commit()

        # Create token pair
        token_pair, token_id, expires_at = create_token_pair(user.id)

        # Store session in Redis
        user_agent = request.headers.get("user-agent") if request else None
        client_ip = request.client.host if request and request.client else None

        await create_session(
            user_id=user.id,
            refresh_token=token_pair.refresh_token,
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=client_ip,
        )

        # Redirect to frontend with tokens
        # In production, you might want to use a more secure method
        # like setting HTTP-only cookies or using a short-lived code
        redirect_url = (
            f"{settings.frontend_url}/auth/callback"
            f"?access_token={token_pair.access_token}"
            f"&refresh_token={token_pair.refresh_token}"
            f"&expires_in={token_pair.expires_in}"
        )

        return RedirectResponse(url=redirect_url)

    except Exception as e:
        logger.exception(f"Google OAuth error: {e}")
        return RedirectResponse(
            url=f"{settings.frontend_url}/login?error=auth_failed"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: TokenRefreshRequest,
    session: AsyncSession = Depends(get_async_session),
) -> TokenResponse:
    """Refresh an access token using a refresh token.

    Args:
        request: Contains the refresh token

    Returns:
        New token pair
    """
    # Verify the refresh token
    token_payload = verify_token(request.refresh_token, expected_type="refresh")
    if token_payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Check if token is revoked
    if not await is_token_valid(request.refresh_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked",
        )

    # Get user
    try:
        user_id = uuid.UUID(token_payload.sub)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or disabled",
        )

    # Revoke old refresh token
    await delete_session_by_token(request.refresh_token)

    # Create new token pair
    token_pair, token_id, expires_at = create_token_pair(user.id)

    # Store new session
    await create_session(
        user_id=user.id,
        refresh_token=token_pair.refresh_token,
        expires_at=expires_at,
    )

    return TokenResponse(
        access_token=token_pair.access_token,
        refresh_token=token_pair.refresh_token,
        expires_in=token_pair.expires_in,
    )


@router.post("/logout")
async def logout(
    request: TokenRefreshRequest,
    user: User = Depends(get_current_user),
) -> dict:
    """Logout and revoke the refresh token.

    Args:
        request: Contains the refresh token to revoke

    Returns:
        Success message
    """
    await delete_session_by_token(request.refresh_token)
    logger.info(f"User logged out: {user.email}")
    return {"ok": True, "message": "Successfully logged out"}


@router.post("/logout-all")
async def logout_all(
    user: User = Depends(get_current_user),
) -> dict:
    """Logout from all devices by revoking all refresh tokens.

    Returns:
        Number of sessions revoked
    """
    count = await delete_all_user_sessions(user.id)
    logger.info(f"User logged out from all devices: {user.email}, {count} sessions")
    return {"ok": True, "message": f"Logged out from {count} sessions"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    user: User = Depends(get_current_user),
) -> UserResponse:
    """Get the current user's information.

    Returns:
        User information
    """
    return UserResponse(
        id=str(user.id),
        email=user.email,
        display_name=user.display_name,
        avatar_url=user.avatar_url,
        timezone=user.timezone,
        created_at=user.created_at,
        user_type=user.user_type,
        initial_balance=user.initial_balance,
    )


@router.get("/status", response_model=AuthStatusResponse)
async def get_auth_status(
    user: Optional[User] = Depends(get_current_user),
) -> AuthStatusResponse:
    """Check authentication status.

    Returns:
        Authentication status with user info if authenticated
    """
    if user is None:
        return AuthStatusResponse(authenticated=False)

    return AuthStatusResponse(
        authenticated=True,
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            display_name=user.display_name,
            avatar_url=user.avatar_url,
            timezone=user.timezone,
            created_at=user.created_at,
            user_type=user.user_type,
            initial_balance=user.initial_balance,
        ),
    )


# =============================================================================
# Child Authentication (Wally Junior)
# =============================================================================


class ChildSignupRequest(BaseModel):
    """Request to create a child account using an invite code."""
    invite_code: str = Field(..., min_length=4, max_length=20, description="Invite code from parent")
    password: str = Field(..., min_length=4, max_length=100, description="Password (min 4 characters)")

    @field_validator("invite_code")
    @classmethod
    def normalize_invite_code(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v.strip()) < 4:
            raise ValueError("Password must be at least 4 characters")
        return v


class ChildLoginRequest(BaseModel):
    """Request to login as a child."""
    email: str = Field(..., min_length=1, max_length=255, description="Child email")
    password: str = Field(..., min_length=1, max_length=100, description="Password")


class ChildUserResponse(BaseModel):
    """Child user information response."""
    id: str
    email: str
    display_name: Optional[str]
    avatar_url: Optional[str]
    user_type: str
    initial_balance: int


@router.post("/child/signup", response_model=TokenResponse)
async def child_signup(
    request: ChildSignupRequest,
    http_request: Request,
    session: AsyncSession = Depends(get_async_session),
) -> TokenResponse:
    """Create a child account using a parent-provided invite code.

    The invite code contains the child's name and initial balance.
    """
    # Find the invite code (no user_id filter - anyone with code can use it)
    result = await session.execute(
        select(InviteCode).where(
            InviteCode.code == request.invite_code.upper(),
            InviteCode.used == False,
            InviteCode.expires_at > datetime.now(timezone.utc),
        )
    )
    invite = result.scalar_one_or_none()

    if invite is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired invite code",
        )

    # Create a unique email for the child (based on parent + child name)
    child_email = f"{invite.child_name.lower().replace(' ', '_')}_{invite.id}@wally.junior"

    # Hash the password using bcrypt (secure password hashing)
    password_hash = bcrypt.hashpw(request.password.encode(), bcrypt.gensalt()).decode()

    # Create the child user
    child = User(
        email=child_email,
        display_name=invite.child_name,
        user_type="child",
        password_hash=password_hash,
        initial_balance=invite.initial_balance,
    )
    session.add(child)
    await session.flush()

    # Mark invite as used
    invite.used = True
    invite.used_by = child.id

    # Create family relationship
    relationship = FamilyRelationship(
        parent_id=invite.parent_id,
        child_id=child.id,
        relationship_type="parent",
    )
    session.add(relationship)

    await session.commit()

    logger.info(f"Created child account: {child_email}")

    # Create token pair
    token_pair, token_id, expires_at = create_token_pair(child.id)

    # Store session
    user_agent = http_request.headers.get("user-agent")
    client_ip = http_request.client.host if http_request.client else None

    await create_session(
        user_id=child.id,
        refresh_token=token_pair.refresh_token,
        expires_at=expires_at,
        user_agent=user_agent,
        ip_address=client_ip,
    )

    return TokenResponse(
        access_token=token_pair.access_token,
        refresh_token=token_pair.refresh_token,
        expires_in=token_pair.expires_in,
    )


@router.post("/child/login", response_model=TokenResponse)
async def child_login(
    request: ChildLoginRequest,
    http_request: Request,
    session: AsyncSession = Depends(get_async_session),
) -> TokenResponse:
    """Login as a child using email and password."""
    # Find the user
    result = await session.execute(
        select(User).where(
            User.email == request.email,
            User.user_type == "child",
        )
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Verify password using bcrypt
    if not user.password_hash or not bcrypt.checkpw(request.password.encode(), user.password_hash.encode()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is disabled",
        )

    # Update last login
    user.last_login_at = datetime.now(timezone.utc)
    await session.commit()

    logger.info(f"Child logged in: {user.email}")

    # Create token pair
    token_pair, token_id, expires_at = create_token_pair(user.id)

    # Store session
    user_agent = http_request.headers.get("user-agent")
    client_ip = http_request.client.host if http_request.client else None

    await create_session(
        user_id=user.id,
        refresh_token=token_pair.refresh_token,
        expires_at=expires_at,
        user_agent=user_agent,
        ip_address=client_ip,
    )

    return TokenResponse(
        access_token=token_pair.access_token,
        refresh_token=token_pair.refresh_token,
        expires_in=token_pair.expires_in,
    )


@router.get("/child/verify-code")
async def verify_invite_code(
    code: str,
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """Verify if an invite code is valid and get child name."""

    result = await session.execute(
        select(InviteCode).where(
            InviteCode.code == code.upper(),
            InviteCode.used == False,
            InviteCode.expires_at > datetime.now(timezone.utc),
        )
    )
    invite = result.scalar_one_or_none()

    if invite is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired invite code",
        )

    return {
        "valid": True,
        "child_name": invite.child_name,
        "initial_balance": invite.initial_balance,
    }
