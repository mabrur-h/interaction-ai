from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from ..config import Settings, get_settings
from ..models import HealthResponse, RootResponse

router = APIRouter(tags=["meta"])


@router.get("/health", response_model=HealthResponse)
def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """Return service health status for monitoring and load balancers."""
    return HealthResponse(ok=True, service="openpoke", version=settings.app_version)


@router.get("/meta", response_model=RootResponse)
def meta(request: Request, settings: Settings = Depends(get_settings)) -> RootResponse:
    """Return service metadata including available API endpoints."""
    endpoints = sorted(
        {
            route.path
            for route in request.app.routes
            if getattr(route, "include_in_schema", False) and route.path.startswith("/api/")
        }
    )
    return RootResponse(
        status="ok",
        service="openpoke",
        version=settings.app_version,
        endpoints=endpoints,
    )
