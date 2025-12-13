"""V2 API Routes - Using PostgreSQL repositories and authentication."""

from server.routes.v2.chat import router as chat_router
from server.routes.v2.gmail import router as gmail_router
from server.routes.v2.calendar import router as calendar_router
from server.routes.v2.meta import router as meta_router

__all__ = ["chat_router", "gmail_router", "calendar_router", "meta_router"]
