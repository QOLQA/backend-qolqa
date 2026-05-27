"""
Shared authentication and authorization dependencies.
"""
from fastapi import Depends, HTTPException, status

from api.handle_errors import handle_common_errors
from domain.entities.auth.UserEntity import UserEntity
from domain.enums.RoleEnum import RoleEnum
from domain.errors import InvalidToken
from infrastructure.jwt import decode_access_token, oauth2_scheme
from infrastructure.repositories.UserRepoImpl import UserRepositoryImpl
from application.use_cases.auth.GetUserById import get_user_by_id
from infrastructure.db_factory import get_database


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


def get_user_repository(database=Depends(get_database)) -> UserRepositoryImpl:
    return UserRepositoryImpl(database)


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
