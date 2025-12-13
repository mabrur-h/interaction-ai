"""V2 Gmail API routes with authentication and PostgreSQL repositories."""

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
from server.services.v2 import GmailService

router = APIRouter(prefix="/gmail", tags=["gmail"])


class GmailConnectRequest(BaseModel):
    """Request body for initiating Gmail connection."""
    auth_config_id: Optional[str] = None


class GmailStatusRequest(BaseModel):
    """Request body for checking Gmail status."""
    connection_request_id: Optional[str] = None


class GmailDisconnectRequest(BaseModel):
    """Request body for disconnecting Gmail."""
    pass


@router.post("/connect")
async def gmail_connect(
    payload: GmailConnectRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    """Initiate Gmail OAuth connection flow through Composio."""
    oauth_repo = OAuthConnectionRepository(session, user.id)
    gmail_service = GmailService(oauth_repo)

    try:
        result = await gmail_service.initiate_connect(
            auth_config_id=payload.auth_config_id or settings.composio_gmail_auth_config_id,
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
            detail=f"Failed to initiate Gmail connect: {exc}",
        )


@router.post("/status")
async def gmail_status(
    payload: GmailStatusRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> JSONResponse:
    """Check the current Gmail connection status."""
    oauth_repo = OAuthConnectionRepository(session, user.id)
    gmail_service = GmailService(oauth_repo)

    try:
        result = await gmail_service.check_status(
            connection_request_id=payload.connection_request_id,
        )
        await session.commit()
        return JSONResponse(result)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check Gmail status: {exc}",
        )


@router.get("/status")
async def gmail_status_get(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> JSONResponse:
    """Get the current Gmail connection status."""
    oauth_repo = OAuthConnectionRepository(session, user.id)
    gmail_service = GmailService(oauth_repo)

    try:
        result = await gmail_service.check_status()
        return JSONResponse(result)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check Gmail status: {exc}",
        )


@router.post("/disconnect")
async def gmail_disconnect(
    payload: GmailDisconnectRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> JSONResponse:
    """Disconnect Gmail account."""
    oauth_repo = OAuthConnectionRepository(session, user.id)
    gmail_service = GmailService(oauth_repo)

    try:
        result = await gmail_service.disconnect()
        await session.commit()
        return JSONResponse(result)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disconnect Gmail: {exc}",
        )


__all__ = ["router"]
