"""
Authentication and authorization dependencies for presentation layer.
"""
from fastapi import Depends, HTTPException, status

from infra.presentation.handle_errors import handle_common_errors
from domain.entities.auth.UserEntity import UserEntity
from domain.enums.RoleEnum import RoleEnum
from domain.errors import InvalidToken
from domain.services.google_auth import IGoogleAuthService
from infra.persistence.jwt import decode_access_token, oauth2_scheme
from infra.persistence.repositories import UserRepositoryImpl
from infra.persistence.security import BcryptHasher
from infra.persistence.services.google_auth import GoogleAuthService
from application.use_cases.auth.GetUserById import get_user_by_id
from infra.presentation.dependencies.common import get_database


def get_token_data(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Extract and validate data from JWT token.
    Raises HTTP 401 if token is invalid or expired.
    """
    try:
        return decode_access_token(token)
    except InvalidToken as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=exc.msg,
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_password_hasher() -> BcryptHasher:
    """Provides the bcrypt password hasher."""
    return BcryptHasher()


def get_google_auth_service() -> IGoogleAuthService:
    """Provides the Google OAuth2 verification service."""
    return GoogleAuthService()


def get_user_repository(
    database=Depends(get_database),
    hasher=Depends(get_password_hasher),
) -> UserRepositoryImpl:
    return UserRepositoryImpl(database, hasher=hasher)


async def get_current_user(
    token_data: dict = Depends(get_token_data),
    repository: UserRepositoryImpl = Depends(get_user_repository),
) -> UserEntity:
    """
    Get current authenticated user from JWT token.
    Validates token_version to detect invalidated tokens.
    """
    username: str = token_data.get("sub")
    user_id: str = token_data.get("user_id")

    if username is None or user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        entity = await get_user_by_id(repository, user_id)

        if not entity.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user",
            )

        # Validate token_version — if mismatch, token was invalidated
        token_version = token_data.get("token_version")
        if token_version is None or token_version != entity.token_version:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been invalidated. Please log in again.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return entity

    except HTTPException:
        raise
    except Exception as exc:
        await handle_common_errors(exc)


async def require_admin(
    token_data: dict = Depends(get_token_data),
    current_user: UserEntity = Depends(get_current_user),
) -> UserEntity:
    """
    Dependency that requires the current user to have admin role.
    Reads roles from JWT payload (no extra DB query).
    Raises HTTP 403 if user is not admin.
    """
    token_roles = token_data.get("roles", [])
    if RoleEnum.admin.value not in token_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


# Auth use cases
def get_register_user_use_case(
    repository=Depends(get_user_repository),
):
    from application.use_cases.auth.RegisterUser import register_user
    return lambda command: register_user(repository, command)


def get_authenticate_user_use_case(
    repository=Depends(get_user_repository),
):
    from application.use_cases.auth.AuthenticateUser import authenticate_user
    return lambda command: authenticate_user(repository, command)


def get_google_login_use_case(
    repository=Depends(get_user_repository),
    google_auth=Depends(get_google_auth_service),
):
    from application.use_cases.auth.GoogleLogin import google_login
    return lambda repository=None, command=None: google_login(
        repository, google_auth, command.credential, command.client_id
    )


def get_get_user_by_id_use_case(
    repository=Depends(get_user_repository),
):
    from application.use_cases.auth.GetUserById import get_user_by_id
    return get_user_by_id