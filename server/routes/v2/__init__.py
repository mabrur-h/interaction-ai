"""V2 API Routes - Using PostgreSQL repositories and authentication."""

from server.routes.v2.chat import router as chat_router
from server.routes.v2.meta import router as meta_router
from server.routes.v2.family import router as family_router
from server.routes.v2.finance import router as finance_router
from server.routes.v2.achievements import router as achievements_router

__all__ = [
    "chat_router",
    "meta_router",
    "family_router",
    "finance_router",
    "achievements_router",
]
