from datetime import timedelta

from application.dtos.auth.AuthResponse import TokenResponse
from auth.jwt import create_access_token
from config.settings import settings
from domain.entities.auth.UserEntity import UserEntity


async def create_user_token(user: UserEntity) -> TokenResponse:
    """
    Create a JWT access token for an authenticated user.

    Args:
        user: UserEntity representing the authenticated user

    Returns:
        TokenResponse with access_token and token_type
    """
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={
            "sub": user.username,
            "user_id": user.id,
            "email": user.email,
        },
        expires_delta=access_token_expires,
    )

    return TokenResponse(access_token=access_token, token_type="bearer")
