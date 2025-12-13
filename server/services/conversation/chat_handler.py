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
from ...services.v2 import ConversationService
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
                # Sync OAuth connections from DB to V1 singletons for execution agents
                await sync_oauth_connections_for_user(session, user_id)

                # Create user-scoped conversation service with the new session
                # auto_commit=True ensures messages are visible to polling immediately
                conv_repo = ConversationRepository(session, user_id)
                wm_repo = WorkingMemoryRepository(session, user_id)
                conv_service = ConversationService(conv_repo, wm_repo, auto_commit=True)

                runtime = InteractionAgentRuntime(conv_service)
                await runtime.execute(user_message=user_content)
            except ValueError as ve:
                # Missing API key error
                logger.error("configuration error", extra={"error": str(ve)})
            except Exception as exc:  # pragma: no cover - defensive
                logger.error("chat task failed", extra={"error": str(exc)}, exc_info=True)

    asyncio.create_task(_run_interaction())

    return PlainTextResponse("", status_code=status.HTTP_202_ACCEPTED)
