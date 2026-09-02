"""
Google OAuth2 ID token verification service.

Lives in infrastructure/ — only layer that imports google-auth.
Uses asyncio.to_thread to keep the event loop free during sync verification.
"""
import asyncio
import logging

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from domain.errors import InvalidGoogleToken

logger = logging.getLogger(__name__)


async def verify_google_token(credential: str, client_id: str) -> dict:
    """
    Verify a Google ID token and extract user claims.

    Args:
        credential: The Google ID token string
        client_id: The expected OAuth2 client ID (audience)

    Returns:
        dict with keys: sub, email, email_verified, name, picture

    Raises:
        InvalidGoogleToken: On any verification failure
    """
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
        raise InvalidGoogleToken()

    if not email:
        raise InvalidGoogleToken()

    if not email_verified:
        raise InvalidGoogleToken()

    return {
        'sub': sub,
        'email': email,
        'email_verified': email_verified,
        'name': idinfo.get('name'),
        'picture': idinfo.get('picture'),
    }
