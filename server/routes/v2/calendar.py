"""V2 Google Calendar API routes with authentication and PostgreSQL repositories."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from server.auth.dependencies import get_current_user
from server.config import Settings, get_settings
from server.database import User
from server.database.session import get_async_session
from server.repositories.oauth_connections import OAuthConnectionRepository
from server.services.v2 import CalendarService

router = APIRouter(prefix="/calendar", tags=["calendar"])


class CalendarConnectRequest(BaseModel):
    """Request body for initiating Calendar connection."""
    auth_config_id: Optional[str] = None


class CalendarStatusRequest(BaseModel):
    """Request body for checking Calendar status."""
    connection_request_id: Optional[str] = None


class CalendarDisconnectRequest(BaseModel):
    """Request body for disconnecting Calendar."""
    pass


@router.post("/connect")
async def calendar_connect(
    payload: CalendarConnectRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    """Initiate Google Calendar OAuth connection flow through Composio."""
    oauth_repo = OAuthConnectionRepository(session, user.id)
    calendar_service = CalendarService(oauth_repo)

    try:
        result = await calendar_service.initiate_connect(
            auth_config_id=payload.auth_config_id or settings.composio_calendar_auth_config_id,
        )
        await session.commit()
        return JSONResponse(result)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate Calendar connect: {exc}",
        )


@router.post("/status")
async def calendar_status(
    payload: CalendarStatusRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> JSONResponse:
    """Check the current Google Calendar connection status."""
    oauth_repo = OAuthConnectionRepository(session, user.id)
    calendar_service = CalendarService(oauth_repo)

    try:
        result = await calendar_service.check_status(
            connection_request_id=payload.connection_request_id,
        )
        await session.commit()
        return JSONResponse(result)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check Calendar status: {exc}",
        )


@router.get("/status")
async def calendar_status_get(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> JSONResponse:
    """Get the current Google Calendar connection status."""
    oauth_repo = OAuthConnectionRepository(session, user.id)
    calendar_service = CalendarService(oauth_repo)

    try:
        result = await calendar_service.check_status()
        return JSONResponse(result)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check Calendar status: {exc}",
        )


@router.post("/disconnect")
async def calendar_disconnect(
    payload: CalendarDisconnectRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> JSONResponse:
    """Disconnect Google Calendar account."""
    oauth_repo = OAuthConnectionRepository(session, user.id)
    calendar_service = CalendarService(oauth_repo)

    try:
        result = await calendar_service.disconnect()
        await session.commit()
        return JSONResponse(result)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disconnect Calendar: {exc}",
        )


__all__ = ["router"]
