import asyncio
import uuid
from typing import Optional, Union

from fastapi import status
from fastapi.responses import JSONResponse, PlainTextResponse

from ...agents.interaction_agent.runtime import InteractionAgentRuntime
from ...logging_config import logger
from ...models import ChatMessage, ChatRequest
from ...repositories.conversations import ConversationRepository
from ...repositories.working_memory import WorkingMemoryRepository
from ...repositories.users import UserRepository
from ...repositories.expenses import ExpenseRepository
from ...repositories.savings_goals import SavingsGoalRepository
from ...repositories.achievements import AchievementRepository
from ...repositories.transactions import TransactionRepository
from ...repositories.budgets import BudgetRepository
from ...repositories.debts import DebtRepository
from ...repositories.recurring_transactions import RecurringTransactionRepository
from ...repositories.exchange_rates import ExchangeRateRepository
from ...services.v2 import ConversationService
from ...services.v2.finance_service import FinanceService
from ...services.v2.achievements_service import AchievementsService
from ...services.v2.adult_finance_service import AdultFinanceService
from ...services.v2.currency_service import CurrencyService
from ...services.execution import UserContext, set_user_context, clear_user_context
from ...utils import error_response


# Extract the most recent user message from the chat request payload
def _extract_latest_user_message(payload: ChatRequest) -> Optional[ChatMessage]:
    for message in reversed(payload.messages):
        if message.role.lower().strip() == "user" and message.content.strip():
            return message
    return None


# Process incoming chat requests by routing them to the interaction agent runtime
async def handle_chat_request(
    payload: ChatRequest,
    user_id: uuid.UUID,
) -> Union[PlainTextResponse, JSONResponse]:
    """Handle a chat request using the InteractionAgentRuntime.

    Args:
        payload: The chat request payload
        user_id: The authenticated user's UUID
    """

    # Extract user message
    user_message = _extract_latest_user_message(payload)
    if user_message is None:
        return error_response("Missing user message", status_code=status.HTTP_400_BAD_REQUEST)

    user_content = user_message.content.strip()  # Already checked in _extract_latest_user_message

    logger.info("chat request", extra={"message_length": len(user_content), "user_id": str(user_id)})

    async def _run_interaction() -> None:
        # Import here to avoid circular imports
        from ...database.session import async_session_factory
        from ...services.oauth_bridge import sync_oauth_connections_for_user

        # Create a new session for the background task
        async with async_session_factory() as session:
            try:
                # Get user to determine user_type (adult vs child)
                user_repo = UserRepository(session)
                user = await user_repo.get_by_id(user_id)
                user_type = user.user_type if user else "adult"

                # Create services based on user type
                finance_service = None
                achievements_service = None
                adult_finance_service = None

                if user_type == "child" and user:
                    # Child users get Wally finance tools
                    expense_repo = ExpenseRepository(session, user_id)
                    savings_repo = SavingsGoalRepository(session, user_id)
                    achievement_repo = AchievementRepository(session, user_id)

                    finance_service = FinanceService(
                        expense_repo=expense_repo,
                        savings_repo=savings_repo,
                        user=user,
                        auto_commit=True,
                    )
                    achievements_service = AchievementsService(
                        achievement_repo=achievement_repo,
                        auto_commit=True,
                    )

                elif user_type == "adult" and user:
                    # Adult users get Poke finance tools
                    transaction_repo = TransactionRepository(session, user_id)
                    budget_repo = BudgetRepository(session, user_id)
                    debt_repo = DebtRepository(session, user_id)
                    recurring_repo = RecurringTransactionRepository(session, user_id)
                    exchange_rate_repo = ExchangeRateRepository(session)

                    currency_service = CurrencyService(exchange_rate_repo)
                    adult_finance_service = AdultFinanceService(
                        transaction_repo=transaction_repo,
                        budget_repo=budget_repo,
                        debt_repo=debt_repo,
                        recurring_repo=recurring_repo,
                        currency_service=currency_service,
                        user=user,
                        auto_commit=True,
                    )

                # Set user context for execution agents
                set_user_context(UserContext(
                    user_id=user_id,
                    user_type=user_type,
                    finance_service=finance_service,
                    achievements_service=achievements_service,
                    adult_finance_service=adult_finance_service,
                ))

                # Sync OAuth connections from DB to V1 singletons for execution agents
                # Only for adult users (kids don't have Gmail/Calendar)
                if user_type == "adult":
                    await sync_oauth_connections_for_user(session, user_id)

                # Create user-scoped conversation service with the new session
                # auto_commit=True ensures messages are visible to polling immediately
                conv_repo = ConversationRepository(session, user_id)
                wm_repo = WorkingMemoryRepository(session, user_id)
                conv_service = ConversationService(conv_repo, wm_repo, auto_commit=True)

                runtime = InteractionAgentRuntime(conv_service, user_type=user_type)
                await runtime.execute(user_message=user_content)
            except ValueError as ve:
                # Missing API key error
                logger.error("configuration error", extra={"error": str(ve)})
            except Exception as exc:  # pragma: no cover - defensive
                logger.error("chat task failed", extra={"error": str(exc)}, exc_info=True)
            finally:
                # Clean up user context
                clear_user_context()

    asyncio.create_task(_run_interaction())

    return PlainTextResponse("", status_code=status.HTTP_202_ACCEPTED)
