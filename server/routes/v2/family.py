"""Family management API routes for Wally Junior."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from server.auth.dependencies import get_current_user
from server.database import User
from server.database.session import get_async_session
from server.repositories.family import FamilyRepository
from server.repositories.invite_codes import InviteCodeRepository
from server.repositories.expenses import ExpenseRepository
from server.repositories.savings_goals import SavingsGoalRepository

router = APIRouter(prefix="/family", tags=["family"])


# =============================================================================
# Request/Response Models
# =============================================================================


class CreateChildInviteRequest(BaseModel):
    """Request to create an invite code for a child."""
    child_name: str = Field(..., min_length=1, max_length=100, description="Child's name")
    initial_balance: float = Field(default=0, ge=0, le=100_000_000, description="Initial balance in so'm")

    @field_validator("child_name")
    @classmethod
    def validate_child_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Child name cannot be empty")
        return v


class CreateChildInviteResponse(BaseModel):
    """Response with the created invite code."""
    code: str
    child_name: str
    initial_balance: int  # In cents
    expires_at: datetime


class ChildSummary(BaseModel):
    """Summary of a child's account."""
    id: str
    display_name: str
    email: Optional[str]
    avatar_url: Optional[str]
    balance: int  # In cents
    spent_this_month: int  # In cents
    active_goals: int
    created_at: datetime


class ExpenseItem(BaseModel):
    """An expense item for display."""
    id: int
    amount: int
    category: str
    description: Optional[str]
    expense_date: datetime


class SavingsGoalItem(BaseModel):
    """A savings goal item for display."""
    id: int
    name: str
    target_amount: int
    current_amount: int
    emoji: Optional[str]


class ChildDetails(BaseModel):
    """Detailed child information including finances."""
    id: str
    display_name: str
    email: Optional[str]
    initial_balance: int
    created_at: datetime
    balance: int
    total_spent: int
    total_saved: int
    recent_expenses: List[ExpenseItem]
    savings_goals: List[SavingsGoalItem]


class PendingInvite(BaseModel):
    """A pending invite code."""
    id: int
    code: str
    child_name: str
    initial_balance: int
    expires_at: datetime
    created_at: datetime


# =============================================================================
# Endpoints
# =============================================================================


@router.post("/create-child", response_model=CreateChildInviteResponse)
async def create_child_invite(
    request: CreateChildInviteRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> CreateChildInviteResponse:
    """Create an invite code for a new child account.

    Only parents (adult users) can create child invites.
    """
    if user.user_type != "adult":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can create child accounts",
        )

    # Store balance as-is (input is in so'm, UZS doesn't commonly use tiyin subdivision)
    # The "cents" naming is a misnomer - we just use whole so'm as the unit
    initial_balance_cents = int(request.initial_balance)

    invite_repo = InviteCodeRepository(session, user.id)
    invite = await invite_repo.create_invite(
        child_name=request.child_name,
        initial_balance=initial_balance_cents,
        expires_in_hours=72,
    )

    await session.commit()

    return CreateChildInviteResponse(
        code=invite.code,
        child_name=invite.child_name,
        initial_balance=invite.initial_balance,
        expires_at=invite.expires_at,
    )


@router.get("/children", response_model=List[ChildSummary])
async def list_children(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> List[ChildSummary]:
    """List all children linked to this parent."""
    if user.user_type != "adult":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can view children",
        )

    family_repo = FamilyRepository(session, user.id)
    children = await family_repo.get_children()

    summaries = []
    for child in children:
        # Get financial stats for each child
        expense_repo = ExpenseRepository(session, child.id)
        savings_repo = SavingsGoalRepository(session, child.id)

        total_spent = await expense_repo.get_total_spent()
        balance = child.initial_balance - total_spent
        active_goals = await savings_repo.get_active_goals()

        # Get spending this month
        from datetime import timedelta
        month_start = datetime.utcnow() - timedelta(days=30)
        spent_this_month = await expense_repo.get_total_spent(start_date=month_start)

        summaries.append(ChildSummary(
            id=str(child.id),
            display_name=child.display_name or "Child",
            email=child.email,
            avatar_url=child.avatar_url,
            balance=balance,
            spent_this_month=spent_this_month,
            active_goals=len(active_goals),
            created_at=child.created_at,
        ))

    return summaries


@router.get("/child/{child_id}", response_model=ChildDetails)
async def get_child(
    child_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> ChildDetails:
    """Get details for a specific child."""
    if user.user_type != "adult":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can view children",
        )

    family_repo = FamilyRepository(session, user.id)

    # Verify this is actually this parent's child
    if not await family_repo.is_parent_of(child_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child not found",
        )

    child_info = await family_repo.get_child_with_stats(child_id)
    if not child_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child not found",
        )

    # Get financial stats
    expense_repo = ExpenseRepository(session, child_id)
    savings_repo = SavingsGoalRepository(session, child_id)

    total_spent = await expense_repo.get_total_spent()
    balance = child_info["initial_balance"] - total_spent
    active_goals = await savings_repo.get_active_goals()
    recent_expenses = await expense_repo.get_expenses(limit=10)

    # Calculate total saved across all goals
    total_saved = sum(goal.current_amount for goal in active_goals)

    return ChildDetails(
        id=child_info["id"],
        display_name=child_info["display_name"] or "Child",
        email=child_info["email"],
        initial_balance=child_info["initial_balance"],
        created_at=child_info["created_at"],
        balance=balance,
        total_spent=total_spent,
        total_saved=total_saved,
        recent_expenses=[
            ExpenseItem(
                id=exp.id,
                amount=exp.amount,
                category=exp.category,
                description=exp.description,
                expense_date=exp.expense_date,
            )
            for exp in recent_expenses
        ],
        savings_goals=[
            SavingsGoalItem(
                id=goal.id,
                name=goal.name,
                target_amount=goal.target_amount,
                current_amount=goal.current_amount,
                emoji=goal.emoji,
            )
            for goal in active_goals
        ],
    )


@router.get("/invites", response_model=List[PendingInvite])
async def list_pending_invites(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> List[PendingInvite]:
    """List all pending (unused) invite codes."""
    if user.user_type != "adult":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can view invites",
        )

    invite_repo = InviteCodeRepository(session, user.id)
    invites = await invite_repo.get_pending_invites()

    return [
        PendingInvite(
            id=inv.id,
            code=inv.code,
            child_name=inv.child_name,
            initial_balance=inv.initial_balance,
            expires_at=inv.expires_at,
            created_at=inv.created_at,
        )
        for inv in invites
    ]


@router.delete("/invite/{invite_id}")
async def cancel_invite(
    invite_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Cancel an unused invite code."""
    if user.user_type != "adult":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can cancel invites",
        )

    invite_repo = InviteCodeRepository(session, user.id)
    deleted = await invite_repo.cancel_invite(invite_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invite not found or already used",
        )

    await session.commit()
    return {"message": "Invite cancelled"}


__all__ = ["router"]
