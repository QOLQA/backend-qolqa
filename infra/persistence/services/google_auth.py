"""
Google OAuth2 ID token verification service (Infrastructure implementation).

Implements domain.services.google_auth.IGoogleAuthService.
Only layer that imports google-auth.
Uses asyncio.to_thread to keep the event loop free during sync verification.
"""
import asyncio
import logging

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from domain.services.google_auth import (
    GoogleAuthInfo,
    GoogleLoginNotConfigured,
    IGoogleAuthService,
    InvalidGoogleToken,
)

logger = logging.getLogger(__name__)


class GoogleAuthService(IGoogleAuthService):
    """Google OAuth2 ID token verification implementation."""

    async def verify_token(self, credential: str, client_id: str) -> GoogleAuthInfo:
        """Verify a Google ID token and extract user claims.

        Args:
            credential: The Google ID token string
            client_id: The expected OAuth2 client ID (audience)

        Returns:
            GoogleAuthInfo with verified user data

        Raises:
            InvalidGoogleToken: On any verification failure
            GoogleLoginNotConfigured: If client_id is None
        """
        if client_id is None:
            raise GoogleLoginNotConfigured()

        try:
            idinfo = await asyncio.to_thread(
                id_token.verify_oauth2_token,
                credential,
                google_requests.Request(),
                client_id,
            )
        except (ValueError, Exception) as exc:
            logger.warning(f"Google token verification failed: {type(exc).__name__}")
            raise InvalidGoogleToken()

        # Validate required claims
        sub = idinfo.get('sub')
        email = idinfo.get('email')
        email_verified = idinfo.get('email_verified', False)

        if not sub:
            exc = InvalidGoogleToken()
            exc.email = email
            raise exc

        if not email:
            raise InvalidGoogleToken()

        if not email_verified:
            exc = InvalidGoogleToken()
            exc.email = email
            raise exc

        return GoogleAuthInfo(
            sub=sub,
            email=email,
            email_verified=email_verified,
            name=idinfo.get('name'),
            picture=idinfo.get('picture'),
        )


# Backward compatibility function (for existing code)
async def verify_google_token(credential: str, client_id: str) -> dict:
    """Legacy function - returns dict instead of GoogleAuthInfo."""
    service = GoogleAuthService()
    info = await service.verify_token(credential, client_id)
    return {
        'sub': info.sub,
        'email': info.email,
        'email_verified': info.email_verified,
        'name': info.name,
        'picture': info.picture,
    }
