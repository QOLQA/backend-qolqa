"""
Token creation service.

Responsible for building JWT access tokens from a UserEntity.
Lives in infrastructure/ because it depends on infrastructure.jwt
and config.settings — both infrastructure concerns.
"""
from datetime import timedelta

from application.dtos.auth.AuthResponse import TokenResponse
from config.settings import settings
from domain.entities.auth.UserEntity import UserEntity
from infrastructure.jwt import create_access_token


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
            "roles": [r.value for r in user.roles],
            "token_version": user.token_version,
        },
        expires_delta=access_token_expires,
    )

    return TokenResponse(access_token=access_token, token_type="bearer")
