"""Finance API routes for Wally Junior - expense tracking and savings goals."""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from server.auth.dependencies import get_current_user
from server.database import User
from server.database.session import get_async_session
from server.repositories.expenses import ExpenseRepository
from server.repositories.savings_goals import SavingsGoalRepository
from server.services.v2 import FinanceService

router = APIRouter(prefix="/finance", tags=["finance"])


# =============================================================================
# Request/Response Models
# =============================================================================


class ExpenseResponse(BaseModel):
    """An expense record."""
    id: int
    amount: int  # In cents
    amount_formatted: str
    category: str
    description: Optional[str]
    expense_date: datetime
    created_at: datetime


class SavingsGoalResponse(BaseModel):
    """A savings goal."""
    id: int
    name: str
    emoji: Optional[str]
    current_amount: int  # In cents
    current_formatted: str
    target_amount: int  # In cents
    target_formatted: str
    progress_percent: float
    status: str
    created_at: datetime
    completed_at: Optional[datetime]


class BalanceResponse(BaseModel):
    """Current balance info."""
    balance: int  # In cents
    balance_formatted: str


class DashboardResponse(BaseModel):
    """Dashboard with all financial info."""
    balance: int
    balance_formatted: str
    spent_this_month: int
    spent_this_month_formatted: str
    active_goals: int
    total_saved: int
    total_saved_formatted: str
    goals: List[dict]


class SpendingSummaryResponse(BaseModel):
    """Spending summary for a period."""
    period: str
    total: int
    total_formatted: str
    by_category: dict
    expense_count: int


VALID_CATEGORIES = ["food", "toys", "games", "clothes", "books", "entertainment", "school", "other"]


class LogExpenseRequest(BaseModel):
    """Request to log an expense."""
    amount: float = Field(..., gt=0, le=100_000_000, description="Amount in so'm (must be positive)")
    category: str = Field(..., min_length=1, max_length=100, description="Expense category")
    description: Optional[str] = Field(None, max_length=500, description="Optional description")

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        v = v.lower().strip()
        if v not in VALID_CATEGORIES:
            raise ValueError(f"Category must be one of: {', '.join(VALID_CATEGORIES)}")
        return v


class CreateGoalRequest(BaseModel):
    """Request to create a savings goal."""
    name: str = Field(..., min_length=1, max_length=255, description="Goal name")
    target_amount: float = Field(..., gt=0, le=100_000_000, description="Target amount in so'm")
    emoji: Optional[str] = Field(None, max_length=10, description="Emoji for the goal")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return v.strip()


class AddToGoalRequest(BaseModel):
    """Request to add money to a goal."""
    amount: float = Field(..., gt=0, le=100_000_000, description="Amount to add in so'm")


# =============================================================================
# Helper
# =============================================================================


def _get_finance_service(
    session: AsyncSession,
    user: User,
) -> FinanceService:
    """Create a FinanceService instance for the user."""
    expense_repo = ExpenseRepository(session, user.id)
    savings_repo = SavingsGoalRepository(session, user.id)
    return FinanceService(expense_repo, savings_repo, user, auto_commit=False)


# =============================================================================
# Endpoints
# =============================================================================


@router.get("/balance", response_model=BalanceResponse)
async def get_balance(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> BalanceResponse:
    """Get current balance."""
    service = _get_finance_service(session, user)
    balance = await service.get_balance()

    return BalanceResponse(
        balance=balance,
        balance_formatted=f"{balance:,} so'm",
    )


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> DashboardResponse:
    """Get financial dashboard with all stats."""
    service = _get_finance_service(session, user)
    stats = await service.get_dashboard_stats()

    return DashboardResponse(
        balance=stats["balance_cents"],
        balance_formatted=f"{stats['balance_cents']:,} so'm",
        spent_this_month=stats["spent_this_month_cents"],
        spent_this_month_formatted=f"{stats['spent_this_month_cents']:,} so'm",
        active_goals=stats["active_goals_count"],
        total_saved=stats["total_saved_cents"],
        total_saved_formatted=f"{stats['total_saved_cents']:,} so'm",
        goals=stats["goals"],
    )


@router.get("/expenses", response_model=List[ExpenseResponse])
async def get_expenses(
    limit: int = Query(default=50, ge=1, le=500, description="Max number of expenses to return"),
    category: Optional[str] = Query(default=None, max_length=100, description="Filter by category"),
    period: Optional[str] = Query(default=None, description="Filter by period: today, week, month, all"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> List[ExpenseResponse]:
    """Get expense history."""
    service = _get_finance_service(session, user)
    expenses = await service.get_expenses(limit=limit, category=category, period=period)

    return [
        ExpenseResponse(
            id=e.id,
            amount=e.amount,
            amount_formatted=f"{e.amount:,} so'm",
            category=e.category,
            description=e.description,
            expense_date=e.expense_date,
            created_at=e.created_at,
        )
        for e in expenses
    ]


@router.post("/expenses", response_model=ExpenseResponse)
async def log_expense(
    request: LogExpenseRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> ExpenseResponse:
    """Log a new expense."""
    service = _get_finance_service(session, user)

    # Store amount as-is (input is in so'm)
    amount_cents = int(request.amount)

    expense = await service.log_expense(
        amount_cents=amount_cents,
        category=request.category,
        description=request.description,
    )

    await session.commit()

    return ExpenseResponse(
        id=expense.id,
        amount=expense.amount,
        amount_formatted=f"{expense.amount:,} so'm",
        category=expense.category,
        description=expense.description,
        expense_date=expense.expense_date,
        created_at=expense.created_at,
    )


@router.get("/spending-summary", response_model=SpendingSummaryResponse)
async def get_spending_summary(
    period: str = "month",
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> SpendingSummaryResponse:
    """Get spending summary for a period."""
    if period not in ["today", "week", "month", "all"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Period must be one of: today, week, month, all",
        )

    service = _get_finance_service(session, user)
    summary = await service.get_spending_summary(period)

    return SpendingSummaryResponse(
        period=summary["period"],
        total=summary["total_cents"],
        total_formatted=f"{summary['total_cents']:,} so'm",
        by_category={k: f"{v:,} so'm" for k, v in summary["by_category"].items()},
        expense_count=summary["count"],
    )


@router.get("/goals", response_model=List[SavingsGoalResponse])
async def get_savings_goals(
    include_completed: bool = False,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> List[SavingsGoalResponse]:
    """Get all savings goals."""
    service = _get_finance_service(session, user)
    goals = await service.list_savings_goals(include_completed=include_completed)

    return [
        SavingsGoalResponse(
            id=g.id,
            name=g.name,
            emoji=g.emoji,
            current_amount=g.current_amount,
            current_formatted=f"{g.current_amount:,} so'm",
            target_amount=g.target_amount,
            target_formatted=f"{g.target_amount:,} so'm",
            progress_percent=round((g.current_amount / g.target_amount) * 100, 1) if g.target_amount > 0 else 0,
            status=g.status,
            created_at=g.created_at,
            completed_at=g.completed_at,
        )
        for g in goals
    ]


@router.post("/goals", response_model=SavingsGoalResponse)
async def create_savings_goal(
    request: CreateGoalRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> SavingsGoalResponse:
    """Create a new savings goal."""
    service = _get_finance_service(session, user)

    # Store amount as-is (input is in so'm)
    target_cents = int(request.target_amount)

    goal = await service.create_savings_goal(
        name=request.name,
        target_amount_cents=target_cents,
        emoji=request.emoji,
    )

    await session.commit()

    return SavingsGoalResponse(
        id=goal.id,
        name=goal.name,
        emoji=goal.emoji,
        current_amount=goal.current_amount,
        current_formatted=f"{goal.current_amount:,} so'm",
        target_amount=goal.target_amount,
        target_formatted=f"{goal.target_amount:,} so'm",
        progress_percent=0,
        status=goal.status,
        created_at=goal.created_at,
        completed_at=goal.completed_at,
    )


@router.post("/goals/{goal_id}/add", response_model=SavingsGoalResponse)
async def add_to_savings_goal(
    goal_id: int,
    request: AddToGoalRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> SavingsGoalResponse:
    """Add money to a savings goal."""
    service = _get_finance_service(session, user)

    # Store amount as-is (input is in so'm)
    amount_cents = int(request.amount)

    goal = await service.add_to_savings(goal_id, amount_cents)

    if goal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found",
        )

    await session.commit()

    return SavingsGoalResponse(
        id=goal.id,
        name=goal.name,
        emoji=goal.emoji,
        current_amount=goal.current_amount,
        current_formatted=f"{goal.current_amount:,} so'm",
        target_amount=goal.target_amount,
        target_formatted=f"{goal.target_amount:,} so'm",
        progress_percent=round((goal.current_amount / goal.target_amount) * 100, 1) if goal.target_amount > 0 else 0,
        status=goal.status,
        created_at=goal.created_at,
        completed_at=goal.completed_at,
    )


@router.delete("/goals/{goal_id}")
async def abandon_goal(
    goal_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Abandon a savings goal."""
    service = _get_finance_service(session, user)
    goal = await service.abandon_goal(goal_id)

    if goal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found",
        )

    await session.commit()
    return {"message": "Goal abandoned"}


__all__ = ["router"]
