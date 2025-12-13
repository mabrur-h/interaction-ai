"""Google OAuth 2.0 authentication."""

import logging
from typing import Any, Optional

import httpx
from pydantic import BaseModel

from server.config import get_settings

logger = logging.getLogger(__name__)


class GoogleUserInfo(BaseModel):
    """Google user information from OAuth."""

    id: str  # Google's unique user ID
    email: str
    verified_email: bool = True
    name: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    picture: Optional[str] = None


class GoogleOAuth:
    """Google OAuth 2.0 client."""

    AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

    # Scopes needed for user authentication
    SCOPES = [
        "openid",
        "email",
        "profile",
    ]

    def __init__(self) -> None:
        self.settings = get_settings()

    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """Generate the Google OAuth authorization URL.

        Args:
            state: Optional state parameter for CSRF protection

        Returns:
            The authorization URL to redirect the user to
        """
        params = {
            "client_id": self.settings.google_client_id,
            "redirect_uri": self.settings.google_redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.SCOPES),
            "access_type": "offline",  # Get refresh token
            "prompt": "consent",  # Always show consent screen for refresh token
        }

        if state:
            params["state"] = state

        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.AUTHORIZATION_URL}?{query_string}"

    async def exchange_code(self, code: str) -> dict[str, Any]:
        """Exchange authorization code for tokens.

        Args:
            code: The authorization code from Google callback

        Returns:
            Token response containing access_token, refresh_token, etc.

        Raises:
            httpx.HTTPStatusError: If the token exchange fails
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.TOKEN_URL,
                data={
                    "client_id": self.settings.google_client_id,
                    "client_secret": self.settings.google_client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": self.settings.google_redirect_uri,
                },
            )
            response.raise_for_status()
            return response.json()

    async def get_user_info(self, access_token: str) -> GoogleUserInfo:
        """Fetch user information from Google.

        Args:
            access_token: Google OAuth access token

        Returns:
            GoogleUserInfo with user's profile data

        Raises:
            httpx.HTTPStatusError: If the request fails
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            data = response.json()

            return GoogleUserInfo(
                id=data["id"],
                email=data["email"],
                verified_email=data.get("verified_email", True),
                name=data.get("name"),
                given_name=data.get("given_name"),
                family_name=data.get("family_name"),
                picture=data.get("picture"),
            )

    async def authenticate(self, code: str) -> GoogleUserInfo:
        """Complete OAuth flow: exchange code and get user info.

        Args:
            code: The authorization code from Google callback

        Returns:
            GoogleUserInfo with user's profile data
        """
        tokens = await self.exchange_code(code)
        access_token = tokens["access_token"]
        return await self.get_user_info(access_token)


# Singleton instance
_google_oauth: Optional[GoogleOAuth] = None


def get_google_oauth() -> GoogleOAuth:
    """Get the Google OAuth client singleton."""
    global _google_oauth
    if _google_oauth is None:
        _google_oauth = GoogleOAuth()
    return _google_oauth
