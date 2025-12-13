from __future__ import annotations

from fastapi import APIRouter

from .auth import router as auth_router
from .meta import router as meta_router

# V2 routes (with authentication and PostgreSQL)
from .v2 import chat_router as chat_router_v2
from .v2 import gmail_router as gmail_router_v2
from .v2 import calendar_router as calendar_router_v2
from .v2 import meta_router as meta_router_v2

# V1 API Router (legacy - auth and health/meta only, no user-specific routes)
api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(meta_router)

# V2 API Router (with auth required for user-specific routes)
api_router_v2 = APIRouter(prefix="/api/v2")
api_router_v2.include_router(auth_router)  # Auth routes same in v2
api_router_v2.include_router(meta_router_v2)
api_router_v2.include_router(chat_router_v2)
api_router_v2.include_router(gmail_router_v2)
api_router_v2.include_router(calendar_router_v2)

__all__ = ["api_router", "api_router_v2"]
