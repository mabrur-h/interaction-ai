"""Repository layer for data access."""

from server.repositories.base import BaseRepository
from server.repositories.users import UserRepository
from server.repositories.conversations import ConversationRepository
from server.repositories.messages import MessageRepository
from server.repositories.oauth_connections import OAuthConnectionRepository
from server.repositories.execution_logs import ExecutionLogRepository
from server.repositories.agent_roster import AgentRosterRepository
from server.repositories.working_memory import WorkingMemoryRepository

# Adult Finance repositories (Poke)
from server.repositories.transactions import TransactionRepository
from server.repositories.budgets import BudgetRepository
from server.repositories.debts import DebtRepository
from server.repositories.recurring_transactions import RecurringTransactionRepository
from server.repositories.exchange_rates import ExchangeRateRepository
from server.repositories.reminder_logs import ReminderLogRepository
from server.repositories.quick_reminders import QuickReminderRepository

__all__ = [
    "BaseRepository",
    "UserRepository",
    "ConversationRepository",
    "MessageRepository",
    "OAuthConnectionRepository",
    "ExecutionLogRepository",
    "AgentRosterRepository",
    "WorkingMemoryRepository",
    # Adult Finance (Poke)
    "TransactionRepository",
    "BudgetRepository",
    "DebtRepository",
    "RecurringTransactionRepository",
    "ExchangeRateRepository",
    "ReminderLogRepository",
    "QuickReminderRepository",
]
