from typing import Optional

from infrastructure.password import verify_password
from domain.entities.auth.UserEntity import UserEntity
from domain.enums.AuthProviderEnum import AuthProviderEnum
from domain.errors import InvalidCredentials, PasswordRequiredForLocalLogin
from infrastructure.repositories.UserRepoImpl import UserRepositoryImpl


async def authenticate_user(
    repository: UserRepositoryImpl,
    username: str,
    password: str,
) -> UserEntity:
    """
    Authenticate a user by username or email and password.

    Args:
        repository: UserRepositoryImpl — typed to access raw credential lookup
        username: Username or email to authenticate
        password: Plain text password

    Returns:
        UserEntity if authentication successful

    Raises:
        InvalidCredentials: If username/password combination is invalid or user is inactive
        PasswordRequiredForLocalLogin: If user has no local password (Google-only account)
    """
    # Try username first, then fall back to email
    user_entity = await repository.get_by_username(username)

    if not user_entity:
        user_entity = await repository.get_by_email(username)

    if not user_entity:
        raise InvalidCredentials()

    # Retrieve hashed_password from the raw document (infra-level detail)
    hashed_password = await repository.get_hashed_password(user_entity.username)

    # Guard: Google-only account has no password — cannot log in via /login
    if (
        user_entity.auth_provider == AuthProviderEnum.google
        and user_entity.is_active
        and hashed_password is None
    ):
        raise PasswordRequiredForLocalLogin()

    if hashed_password is None or not verify_password(password, hashed_password):
        raise InvalidCredentials()

    if not user_entity.is_active:
        raise InvalidCredentials()

    return user_entity
