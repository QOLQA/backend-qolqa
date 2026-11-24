"""
Google Authentication service port (Domain layer).

Defines the contract for verifying Google OAuth tokens.
Implementation lives in infrastructure/services/.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass

from domain.errors import InvalidGoogleToken as BaseInvalidGoogleToken


@dataclass(frozen=True)
class GoogleAuthInfo:
    """Verified Google token information."""
    sub: str                    # Google user ID
    email: str
    email_verified: bool
    name: str | None = None
    picture: str | None = None


class IGoogleAuthService(ABC):
    """Port for Google OAuth token verification."""

    @abstractmethod
    async def verify_token(self, credential: str, client_id: str) -> GoogleAuthInfo:
        """Verify a Google ID token and return user info.

        Args:
            credential: Google ID token from client
            client_id: Expected audience (Google OAuth client ID)

        Returns:
            GoogleAuthInfo with verified user data

        Raises:
            InvalidGoogleToken: If token verification fails
            GoogleLoginNotConfigured: If client_id is None
        """
        ...


class InvalidGoogleToken(BaseInvalidGoogleToken):
    """Raised when Google token verification fails."""


class GoogleLoginNotConfigured(Exception):
    """Raised when Google OAuth is not configured (missing client_id)."""
