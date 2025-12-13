"""V2 Meta API routes with authentication and PostgreSQL repositories."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from server.auth.dependencies import get_current_user, get_current_user_optional
from server.config import Settings, get_settings
from server.database import User
from server.database.session import get_async_session
from server.models import HealthResponse, RootResponse

router = APIRouter(tags=["meta"])


class SetTimezoneRequest(BaseModel):
    """Request body for setting timezone."""
    timezone: str


class SetTimezoneResponse(BaseModel):
    """Response for timezone operations."""
    timezone: str


class UserProfileResponse(BaseModel):
    """User profile response."""
    id: str
    email: str
    display_name: Optional[str]
    avatar_url: Optional[str]
    timezone: str


@router.get("/health", response_model=HealthResponse)
def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """Return service health status for monitoring and load balancers."""
    return HealthResponse(ok=True, service="openpoke", version=settings.app_version)


@router.get("/meta", response_model=RootResponse)
def meta(request: Request, settings: Settings = Depends(get_settings)) -> RootResponse:
    """Return service metadata including available API endpoints."""
    endpoints = sorted(
        {
            route.path
            for route in request.app.routes
            if getattr(route, "include_in_schema", False) and route.path.startswith("/api/")
        }
    )
    return RootResponse(
        status="ok",
        service="openpoke",
        version=settings.app_version,
        endpoints=endpoints,
    )


@router.get("/meta/profile", response_model=UserProfileResponse)
async def get_profile(
    user: User = Depends(get_current_user),
) -> UserProfileResponse:
    """Get the current user's profile."""
    return UserProfileResponse(
        id=str(user.id),
        email=user.email,
        display_name=user.display_name,
        avatar_url=user.avatar_url,
        timezone=user.timezone,
    )


@router.post("/meta/timezone", response_model=SetTimezoneResponse)
async def set_timezone(
    payload: SetTimezoneRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> SetTimezoneResponse:
    """Set the user's timezone."""
    # Validate timezone
    timezone_name = payload.timezone.strip()
    if not timezone_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Timezone must be a non-empty string",
        )

    try:
        ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown timezone: {timezone_name}",
        )

    # Update user's timezone
    await session.execute(
        update(User).where(User.id == user.id).values(timezone=timezone_name)
    )
    await session.commit()

    return SetTimezoneResponse(timezone=timezone_name)


@router.get("/meta/timezone", response_model=SetTimezoneResponse)
async def get_timezone(
    user: User = Depends(get_current_user),
) -> SetTimezoneResponse:
    """Get the user's current timezone."""
    return SetTimezoneResponse(timezone=user.timezone)


__all__ = ["router"]
