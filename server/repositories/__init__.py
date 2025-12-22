"""Repository layer for data access."""

from server.repositories.base import BaseRepository
from server.repositories.users import UserRepository
from server.repositories.conversations import ConversationRepository
from server.repositories.messages import MessageRepository
from server.repositories.oauth_connections import OAuthConnectionRepository
from server.repositories.execution_logs import ExecutionLogRepository
from server.repositories.agent_roster import AgentRosterRepository
from server.repositories.working_memory import WorkingMemoryRepository

# Wally Junior repositories
from server.repositories.expenses import ExpenseRepository
from server.repositories.savings_goals import SavingsGoalRepository
from server.repositories.family import FamilyRepository
from server.repositories.invite_codes import InviteCodeRepository

# Adult Finance repositories (Poke)
from server.repositories.transactions import TransactionRepository
from server.repositories.budgets import BudgetRepository
from server.repositories.debts import DebtRepository
from server.repositories.recurring_transactions import RecurringTransactionRepository
from server.repositories.exchange_rates import ExchangeRateRepository

__all__ = [
    "BaseRepository",
    "UserRepository",
    "ConversationRepository",
    "MessageRepository",
    "OAuthConnectionRepository",
    "ExecutionLogRepository",
    "AgentRosterRepository",
    "WorkingMemoryRepository",
    # Wally Junior
    "ExpenseRepository",
    "SavingsGoalRepository",
    "FamilyRepository",
    "InviteCodeRepository",
    # Adult Finance (Poke)
    "TransactionRepository",
    "BudgetRepository",
    "DebtRepository",
    "RecurringTransactionRepository",
    "ExchangeRateRepository",
]
