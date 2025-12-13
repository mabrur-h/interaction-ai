"""V2 Chat API routes with authentication and PostgreSQL repositories."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from server.auth.dependencies import get_current_user
from server.database import User
from server.database.session import get_async_session
from server.models import ChatHistoryClearResponse, ChatHistoryResponse, ChatRequest
from server.repositories.conversations import ConversationRepository
from server.repositories.triggers import TriggerRepository
from server.repositories.execution_logs import ExecutionLogRepository
from server.repositories.agent_roster import AgentRosterRepository
from server.repositories.working_memory import WorkingMemoryRepository
from server.services.v2 import ConversationService, TriggerService

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/send", response_class=JSONResponse, summary="Submit a chat message")
async def chat_send(
    payload: ChatRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> JSONResponse:
    """Handle incoming chat messages and route them to the interaction agent."""
    # For now, we still use the legacy handler but will need to update it
    # to use the new v2 services with user context
    from server.services import handle_chat_request
    return await handle_chat_request(payload)


@router.get("/history", response_model=ChatHistoryResponse)
async def chat_history(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> ChatHistoryResponse:
    """Retrieve the conversation history for the authenticated user."""
    conv_repo = ConversationRepository(session, user.id)
    wm_repo = WorkingMemoryRepository(session, user.id)
    conv_service = ConversationService(conv_repo, wm_repo)

    messages = await conv_service.to_chat_messages()
    return ChatHistoryResponse(messages=messages)


@router.delete("/history", response_model=ChatHistoryClearResponse)
async def clear_history(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> ChatHistoryClearResponse:
    """Clear all conversation data for the authenticated user."""
    # Clear conversation and working memory
    conv_repo = ConversationRepository(session, user.id)
    wm_repo = WorkingMemoryRepository(session, user.id)
    conv_service = ConversationService(conv_repo, wm_repo)
    await conv_service.clear()

    # Clear triggers
    trigger_repo = TriggerRepository(session, user.id)
    await trigger_repo.clear_all()

    # Clear agent roster
    roster_repo = AgentRosterRepository(session, user.id)
    agents = await roster_repo.get_agent_names()
    for agent_name in agents:
        await roster_repo.unregister_agent(agent_name)

    # Commit all changes
    await session.commit()

    return ChatHistoryClearResponse()


__all__ = ["router"]
