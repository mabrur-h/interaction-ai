"""Database module for OpenPoke."""

from server.database.session import get_async_session, AsyncSessionLocal
from server.database.models import (
    Base,
    User,
    Session,
    OAuthConnection,
    Conversation,
    Message,
    ExecutionLog,
    AgentRoster,
    WorkingMemory,
    # Wally Junior models
    FamilyRelationship,
    Expense,
    SavingsGoal,
    InviteCode,
    Achievement,
    # Adult Finance models (Poke)
    Transaction,
    Budget,
    Debt,
    RecurringTransaction,
    ExchangeRate,
)

__all__ = [
    # Session
    "get_async_session",
    "AsyncSessionLocal",
    # Models
    "Base",
    "User",
    "Session",
    "OAuthConnection",
    "Conversation",
    "Message",
    "ExecutionLog",
    "AgentRoster",
    "WorkingMemory",
    # Wally Junior
    "FamilyRelationship",
    "Expense",
    "SavingsGoal",
    "InviteCode",
    "Achievement",
    # Adult Finance (Poke)
    "Transaction",
    "Budget",
    "Debt",
    "RecurringTransaction",
    "ExchangeRate",
]
