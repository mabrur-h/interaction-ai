"""Google Calendar service client using Composio SDK."""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import status
from fastapi.responses import JSONResponse

from ...config import Settings, get_settings
from ...logging_config import logger
from ...models import CalendarConnectPayload, CalendarDisconnectPayload, CalendarStatusPayload
from ...utils import error_response


_CLIENT_LOCK = threading.Lock()
_CLIENT: Optional[Any] = None

_ACTIVE_USER_ID_LOCK = threading.Lock()
_ACTIVE_USER_ID: Optional[str] = None


def _normalized(value: Optional[str]) -> str:
    return (value or "").strip()


def _set_active_calendar_user_id(user_id: Optional[str]) -> None:
    sanitized = _normalized(user_id)
    with _ACTIVE_USER_ID_LOCK:
        global _ACTIVE_USER_ID
        _ACTIVE_USER_ID = sanitized or None


def get_active_calendar_user_id() -> Optional[str]:
    with _ACTIVE_USER_ID_LOCK:
        return _ACTIVE_USER_ID


def _calendar_import_client():
    from composio import Composio  # type: ignore
    return Composio


def _get_composio_client(settings: Optional[Settings] = None):
    """Get or create a singleton Composio client instance with thread-safe initialization."""
    global _CLIENT
    if _CLIENT is not None:
        return _CLIENT

    with _CLIENT_LOCK:
        if _CLIENT is None:
            resolved_settings = settings or get_settings()
            Composio = _calendar_import_client()
            api_key = resolved_settings.composio_api_key
            try:
                _CLIENT = Composio(api_key=api_key) if api_key else Composio()
            except TypeError as exc:
                if api_key:
                    raise RuntimeError(
                        "Installed Composio SDK does not accept the api_key argument; upgrade the SDK or remove COMPOSIO_API_KEY."
                    ) from exc
                _CLIENT = Composio()
    return _CLIENT


def _extract_email(obj: Any) -> Optional[str]:
    """Extract email address from various response formats."""
    if obj is None:
        return None
    direct_keys = (
        "email",
        "email_address",
        "emailAddress",
        "user_email",
        "provider_email",
        "account_email",
    )
    for key in direct_keys:
        try:
            val = getattr(obj, key)
            if isinstance(val, str) and "@" in val:
                return val
        except Exception:
            pass
        if isinstance(obj, dict):
            val = obj.get(key)
            if isinstance(val, str) and "@" in val:
                return val
    return None


def initiate_connect(payload: CalendarConnectPayload, settings: Settings) -> JSONResponse:
    """Start Google Calendar OAuth connection process and return redirect URL."""
    auth_config_id = payload.auth_config_id or settings.composio_calendar_auth_config_id or ""
    if not auth_config_id:
        return error_response(
            "Missing auth_config_id. Set COMPOSIO_CALENDAR_AUTH_CONFIG_ID or pass auth_config_id.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    user_id = payload.user_id or f"web-{os.getpid()}"
    _set_active_calendar_user_id(user_id)
    try:
        client = _get_composio_client(settings)
        req = client.connected_accounts.initiate(
            user_id=user_id,
            auth_config_id=auth_config_id,
            allow_multiple=True,
        )
        data = {
            "ok": True,
            "redirect_url": getattr(req, "redirect_url", None) or getattr(req, "redirectUrl", None),
            "connection_request_id": getattr(req, "id", None),
            "user_id": user_id,
        }
        return JSONResponse(data)
    except Exception as exc:
        logger.exception("calendar connect failed", extra={"user_id": user_id})
        return error_response(
            "Failed to initiate Calendar connect",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


def fetch_status(payload: CalendarStatusPayload) -> JSONResponse:
    """Check Google Calendar connection status and retrieve user account information."""
    connection_request_id = _normalized(payload.connection_request_id)
    user_id = _normalized(payload.user_id)

    if not connection_request_id and not user_id:
        return error_response(
            "Missing connection_request_id or user_id",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    try:
        client = _get_composio_client()
        account: Any = None
        if connection_request_id:
            try:
                account = client.connected_accounts.wait_for_connection(connection_request_id, timeout=2.0)
            except Exception:
                try:
                    account = client.connected_accounts.get(connection_request_id)
                except Exception:
                    account = None
        if account is None and user_id:
            try:
                items = client.connected_accounts.list(
                    user_ids=[user_id], toolkit_slugs=["GOOGLECALENDAR"], statuses=["ACTIVE"]
                )
                data = getattr(items, "data", None)
                if data is None and isinstance(items, dict):
                    data = items.get("data")
                if data:
                    account = data[0]
            except Exception:
                account = None

        status_value = None
        email = None
        connected = False
        account_user_id = None

        if account is not None:
            status_value = getattr(account, "status", None) or (account.get("status") if isinstance(account, dict) else None)
            normalized_status = (status_value or "").upper()
            connected = normalized_status in {"CONNECTED", "SUCCESS", "SUCCESSFUL", "ACTIVE", "COMPLETED"}
            email = _extract_email(account)
            if hasattr(account, "user_id"):
                account_user_id = getattr(account, "user_id", None)
            elif isinstance(account, dict):
                account_user_id = account.get("user_id")

        if not user_id and account_user_id:
            user_id = _normalized(account_user_id)

        _set_active_calendar_user_id(user_id)

        return JSONResponse(
            {
                "ok": True,
                "connected": bool(connected),
                "status": status_value or "UNKNOWN",
                "email": email,
                "user_id": user_id,
            }
        )
    except Exception as exc:
        logger.exception(
            "calendar status failed",
            extra={
                "connection_request_id": connection_request_id,
                "user_id": user_id,
            },
        )
        return error_response(
            "Failed to fetch connection status",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


def disconnect_account(payload: CalendarDisconnectPayload) -> JSONResponse:
    """Disconnect Google Calendar account."""
    connection_id = _normalized(payload.connection_id) or _normalized(payload.connection_request_id)
    user_id = _normalized(payload.user_id)

    if not connection_id and not user_id:
        return error_response(
            "Missing connection_id or user_id",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    try:
        client = _get_composio_client()
    except Exception as exc:
        logger.exception("calendar disconnect failed: client init", extra={"user_id": user_id})
        return error_response(
            "Failed to disconnect Calendar",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )

    removed_ids: list[str] = []
    errors: list[str] = []
    affected_user_ids: set[str] = set()

    def _delete_connection(identifier: str) -> None:
        sanitized_id = _normalized(identifier)
        if not sanitized_id:
            return
        try:
            connection = client.connected_accounts.get(sanitized_id)
        except Exception:
            connection = None
        try:
            client.connected_accounts.delete(sanitized_id)
            removed_ids.append(sanitized_id)
            if connection is not None:
                if hasattr(connection, "user_id"):
                    affected_user_ids.add(_normalized(getattr(connection, "user_id", None)))
                elif isinstance(connection, dict):
                    affected_user_ids.add(_normalized(connection.get("user_id")))
        except Exception as exc:
            logger.exception("Failed to remove Calendar connection", extra={"connection_id": sanitized_id})
            errors.append(str(exc))

    if connection_id:
        _delete_connection(connection_id)
    else:
        try:
            items = client.connected_accounts.list(user_ids=[user_id], toolkit_slugs=["GOOGLECALENDAR"])
            data = getattr(items, "data", None)
            if data is None and isinstance(items, dict):
                data = items.get("data")
        except Exception as exc:
            logger.exception("Failed to list Calendar connections", extra={"user_id": user_id})
            return error_response(
                "Failed to disconnect Calendar",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(exc),
            )

        if data:
            for entry in data:
                candidate = None
                candidate_user_id = None
                if hasattr(entry, "id"):
                    candidate = getattr(entry, "id", None)
                    candidate_user_id = getattr(entry, "user_id", None)
                if candidate is None and isinstance(entry, dict):
                    candidate = entry.get("id")
                    candidate_user_id = entry.get("user_id")
                if candidate:
                    if candidate_user_id:
                        affected_user_ids.add(_normalized(candidate_user_id))
                    _delete_connection(candidate)

    if user_id:
        affected_user_ids.add(user_id)

    for uid in list(affected_user_ids):
        if uid and get_active_calendar_user_id() == uid:
            _set_active_calendar_user_id(None)

    if errors and not removed_ids:
        return error_response(
            "Failed to disconnect Calendar",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="; ".join(errors),
        )

    response_payload = {
        "ok": True,
        "disconnected": bool(removed_ids),
        "removed_connection_ids": removed_ids,
    }
    if not removed_ids:
        response_payload["message"] = "No Calendar connection found"

    if errors:
        response_payload["warnings"] = errors
    return JSONResponse(response_payload)


def _normalize_tool_response(result: Any) -> Dict[str, Any]:
    """Normalize Composio SDK response to a dictionary."""
    payload_dict: Optional[Dict[str, Any]] = None
    try:
        if hasattr(result, "model_dump"):
            payload_dict = result.model_dump()
        elif hasattr(result, "dict"):
            payload_dict = result.dict()
    except Exception:
        payload_dict = None

    if payload_dict is None:
        try:
            if hasattr(result, "model_dump_json"):
                payload_dict = json.loads(result.model_dump_json())
        except Exception:
            payload_dict = None

    if payload_dict is None:
        if isinstance(result, dict):
            payload_dict = result
        elif isinstance(result, list):
            payload_dict = {"items": result}
        else:
            payload_dict = {"repr": str(result)}

    return payload_dict


def execute_calendar_tool(
    tool_name: str,
    composio_user_id: str,
    *,
    arguments: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Execute Google Calendar operations through Composio SDK with error handling."""
    prepared_arguments: Dict[str, Any] = {}
    if isinstance(arguments, dict):
        for key, value in arguments.items():
            if value is not None:
                prepared_arguments[key] = value

    try:
        client = _get_composio_client()
        result = client.client.tools.execute(
            tool_name,
            user_id=composio_user_id,
            arguments=prepared_arguments,
        )
        return _normalize_tool_response(result)
    except Exception as exc:
        logger.exception(
            "calendar tool execution failed",
            extra={"tool": tool_name, "user_id": composio_user_id},
        )
        raise RuntimeError(f"{tool_name} invocation failed: {exc}") from exc
