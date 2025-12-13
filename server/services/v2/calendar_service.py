"""Async Google Calendar service using PostgreSQL repositories."""

from __future__ import annotations

import json
import threading
from typing import Any, Dict, Optional

from server.config import Settings, get_settings
from server.database.models import OAuthConnection
from server.logging_config import logger
from server.repositories.oauth_connections import OAuthConnectionRepository


# Composio client singleton (thread-safe)
_CLIENT_LOCK = threading.Lock()
_CLIENT: Optional[Any] = None


def _calendar_import_client():
    """Lazy import Composio client."""
    from composio import Composio  # type: ignore
    return Composio


def _get_composio_client(settings: Optional[Settings] = None) -> Any:
    """Get or create singleton Composio client."""
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
                        "Installed Composio SDK does not accept the api_key argument"
                    ) from exc
                _CLIENT = Composio()
    return _CLIENT


def _normalized(value: Optional[str]) -> str:
    """Normalize string value."""
    return (value or "").strip()


def _extract_email(obj: Any) -> Optional[str]:
    """Extract email address from various response formats."""
    if obj is None:
        return None

    direct_keys = (
        "email", "email_address", "emailAddress", "user_email",
        "provider_email", "account_email",
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


def _normalize_tool_response(result: Any) -> Dict[str, Any]:
    """Convert Composio SDK response to dict."""
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


class CalendarService:
    """Async Google Calendar service with user-scoped OAuth connections.

    This is the v2 version that stores OAuth connections in PostgreSQL
    instead of using global singletons.
    """

    def __init__(self, oauth_repo: OAuthConnectionRepository):
        """Initialize with OAuth repository.

        Args:
            oauth_repo: OAuthConnectionRepository instance (user-scoped)
        """
        self._oauth_repo = oauth_repo

    async def get_connection(self) -> Optional[OAuthConnection]:
        """Get the user's Calendar connection.

        Returns:
            The OAuthConnection or None
        """
        return await self._oauth_repo.get_calendar_connection()

    async def get_composio_user_id(self) -> Optional[str]:
        """Get the Composio user ID for Calendar.

        Returns:
            The Composio user ID or None
        """
        conn = await self.get_connection()
        return conn.composio_user_id if conn else None

    async def is_connected(self) -> bool:
        """Check if Calendar is connected.

        Returns:
            True if connected and active
        """
        conn = await self.get_connection()
        return conn is not None and conn.status == "active"

    async def initiate_connect(
        self,
        auth_config_id: Optional[str] = None,
        user_id_suffix: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Initiate Calendar OAuth connection.

        Args:
            auth_config_id: Composio auth config ID
            user_id_suffix: Optional suffix for composio user ID

        Returns:
            Dict with redirect_url and connection info
        """
        settings = get_settings()
        resolved_auth_config = auth_config_id or settings.composio_calendar_auth_config_id
        if not resolved_auth_config:
            raise ValueError(
                "Missing auth_config_id. Set COMPOSIO_CALENDAR_AUTH_CONFIG_ID or pass auth_config_id."
            )

        # Generate composio user ID based on our user ID
        composio_user_id = f"user-{self._oauth_repo.user_id}-calendar"
        if user_id_suffix:
            composio_user_id = f"{composio_user_id}-{user_id_suffix}"

        client = _get_composio_client(settings)
        req = client.connected_accounts.initiate(
            user_id=composio_user_id,
            auth_config_id=resolved_auth_config,
            allow_multiple=True,
        )

        connection_request_id = getattr(req, "id", None)
        redirect_url = getattr(req, "redirect_url", None) or getattr(req, "redirectUrl", None)

        # Store pending connection
        await self._oauth_repo.upsert_connection(
            provider="calendar",
            composio_user_id=composio_user_id,
            composio_connection_id=connection_request_id,
            status="pending",
            extra_data={"connection_request_id": connection_request_id},
        )

        return {
            "ok": True,
            "redirect_url": redirect_url,
            "connection_request_id": connection_request_id,
            "composio_user_id": composio_user_id,
        }

    async def check_status(
        self,
        connection_request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Check Calendar connection status.

        Args:
            connection_request_id: Optional connection request ID to check

        Returns:
            Dict with connection status
        """
        conn = await self.get_connection()
        if conn is None and not connection_request_id:
            return {
                "ok": True,
                "connected": False,
                "status": "NOT_CONNECTED",
                "email": None,
            }

        composio_user_id = conn.composio_user_id if conn else None
        check_id = connection_request_id or (conn.composio_connection_id if conn else None)

        client = _get_composio_client()
        account: Any = None

        # Try to get connection status
        if check_id:
            try:
                account = client.connected_accounts.wait_for_connection(check_id, timeout=2.0)
            except Exception:
                try:
                    account = client.connected_accounts.get(check_id)
                except Exception:
                    account = None

        if account is None and composio_user_id:
            try:
                items = client.connected_accounts.list(
                    user_ids=[composio_user_id],
                    toolkit_slugs=["GOOGLECALENDAR"],
                    statuses=["ACTIVE"],
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

        if account is not None:
            status_value = getattr(account, "status", None)
            if status_value is None and isinstance(account, dict):
                status_value = account.get("status")

            normalized_status = (status_value or "").upper()
            connected = normalized_status in {
                "CONNECTED", "SUCCESS", "SUCCESSFUL", "ACTIVE", "COMPLETED"
            }
            email = _extract_email(account)

        # Update connection in database
        if conn:
            new_status = "active" if connected else "disconnected"
            await self._oauth_repo.update_status(
                provider="calendar",
                status=new_status,
                provider_email=email,
            )

        return {
            "ok": True,
            "connected": connected,
            "status": status_value or "UNKNOWN",
            "email": email,
            "composio_user_id": composio_user_id,
        }

    async def disconnect(self) -> Dict[str, Any]:
        """Disconnect Calendar account.

        Returns:
            Dict with disconnection status
        """
        conn = await self.get_connection()
        if conn is None:
            return {
                "ok": True,
                "disconnected": False,
                "message": "No Calendar connection found",
            }

        removed_ids: list[str] = []
        errors: list[str] = []

        client = _get_composio_client()

        # Try to delete from Composio
        if conn.composio_connection_id:
            try:
                client.connected_accounts.delete(conn.composio_connection_id)
                removed_ids.append(conn.composio_connection_id)
            except Exception as exc:
                logger.warning(f"Failed to delete connection from Composio: {exc}")
                errors.append(str(exc))

        # Also try listing and deleting by user_id
        if conn.composio_user_id:
            try:
                items = client.connected_accounts.list(
                    user_ids=[conn.composio_user_id],
                    toolkit_slugs=["GOOGLECALENDAR"],
                )
                data = getattr(items, "data", None)
                if data is None and isinstance(items, dict):
                    data = items.get("data")
                if data:
                    for entry in data:
                        entry_id = getattr(entry, "id", None)
                        if entry_id is None and isinstance(entry, dict):
                            entry_id = entry.get("id")
                        if entry_id and entry_id not in removed_ids:
                            try:
                                client.connected_accounts.delete(entry_id)
                                removed_ids.append(entry_id)
                            except Exception as exc:
                                errors.append(str(exc))
            except Exception as exc:
                logger.warning(f"Failed to list Calendar connections: {exc}")

        # Delete from database
        await self._oauth_repo.disconnect("calendar")

        result = {
            "ok": True,
            "disconnected": bool(removed_ids),
            "removed_connection_ids": removed_ids,
        }
        if errors:
            result["warnings"] = errors
        if not removed_ids:
            result["message"] = "Connection removed from database"

        return result

    async def execute_tool(
        self,
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute a Calendar tool through Composio.

        Args:
            tool_name: Composio tool name
            arguments: Tool arguments

        Returns:
            Tool execution result
        """
        composio_user_id = await self.get_composio_user_id()
        if not composio_user_id:
            raise RuntimeError("Calendar not connected")

        prepared_args: Dict[str, Any] = {}
        if isinstance(arguments, dict):
            for key, value in arguments.items():
                if value is not None:
                    prepared_args[key] = value

        try:
            client = _get_composio_client()
            result = client.client.tools.execute(
                tool_name,
                user_id=composio_user_id,
                arguments=prepared_args,
            )
            return _normalize_tool_response(result)
        except Exception as exc:
            logger.exception(
                "Calendar tool execution failed",
                extra={"tool": tool_name, "user_id": composio_user_id},
            )
            raise RuntimeError(f"{tool_name} invocation failed: {exc}") from exc


__all__ = ["CalendarService"]
