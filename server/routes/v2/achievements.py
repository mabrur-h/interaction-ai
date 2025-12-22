"""Achievements API routes for Wally Junior - badges and rewards for kids."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from server.auth.dependencies import get_current_user
from server.database import User
from server.database.session import get_async_session
from server.repositories.achievements import AchievementRepository, ACHIEVEMENT_DEFINITIONS
from server.services.v2 import AchievementsService

router = APIRouter(prefix="/achievements", tags=["achievements"])


# =============================================================================
# Response Models
# =============================================================================


class AchievementResponse(BaseModel):
    """A single achievement."""
    type: str
    name: str
    description: str
    emoji: str
    earned: bool
    earned_at: str | None = None


class AchievementProgressResponse(BaseModel):
    """Achievement progress summary."""
    earned: int
    total: int
    progress_percent: float
    remaining: int


class EarnedAchievementResponse(BaseModel):
    """An earned achievement with details."""
    id: int
    type: str
    name: str
    description: str
    emoji: str
    earned_at: str
    metadata: dict


# =============================================================================
# Helper
# =============================================================================


def _get_achievements_service(
    session: AsyncSession,
    user: User,
) -> AchievementsService:
    """Create an AchievementsService instance for the user."""
    achievement_repo = AchievementRepository(session, user.id)
    return AchievementsService(achievement_repo, auto_commit=False)


# =============================================================================
# Endpoints
# =============================================================================


@router.get("", response_model=List[EarnedAchievementResponse])
async def get_earned_achievements(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> List[EarnedAchievementResponse]:
    """Get all achievements earned by the user."""
    if user.user_type != "child":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Achievements are only available for children",
        )

    service = _get_achievements_service(session, user)
    achievements = await service.get_achievements()

    return [
        EarnedAchievementResponse(
            id=a["id"],
            type=a["type"],
            name=a["name"],
            description=a["description"],
            emoji=a["emoji"],
            earned_at=a["earned_at"],
            metadata=a["metadata"],
        )
        for a in achievements
    ]


@router.get("/all", response_model=List[AchievementResponse])
async def get_all_achievements(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> List[AchievementResponse]:
    """Get all possible achievements with earned status."""
    if user.user_type != "child":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Achievements are only available for children",
        )

    service = _get_achievements_service(session, user)
    all_achievements = await service.get_all_achievements()

    return [
        AchievementResponse(
            type=a["type"],
            name=a["name"],
            description=a["description"],
            emoji=a["emoji"],
            earned=a["earned"],
            earned_at=a["earned_at"],
        )
        for a in all_achievements
    ]


@router.get("/progress", response_model=AchievementProgressResponse)
async def get_achievement_progress(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> AchievementProgressResponse:
    """Get achievement progress summary."""
    if user.user_type != "child":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Achievements are only available for children",
        )

    service = _get_achievements_service(session, user)
    progress = await service.get_achievement_progress()

    return AchievementProgressResponse(
        earned=progress["earned"],
        total=progress["total"],
        progress_percent=progress["progress_percent"],
        remaining=progress["remaining"],
    )


@router.get("/definitions")
async def get_achievement_definitions() -> dict:
    """Get all achievement type definitions (public, no auth required)."""
    return {
        "achievements": [
            {
                "type": ach_type,
                "name": definition["name"],
                "description": definition["description"],
                "emoji": definition["emoji"],
            }
            for ach_type, definition in ACHIEVEMENT_DEFINITIONS.items()
        ],
        "total": len(ACHIEVEMENT_DEFINITIONS),
    }


__all__ = ["router"]
