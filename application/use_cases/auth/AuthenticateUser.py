from typing import Optional

from infrastructure.password import verify_password
from domain.entities.auth.UserEntity import UserEntity
from infrastructure.repositories.UserRepoImpl import UserRepositoryImpl


async def authenticate_user(
    repository: UserRepositoryImpl,
    username: str,
    password: str,
) -> Optional[UserEntity]:
    """
    Authenticate a user by username or email and password.

    Args:
        repository: UserRepositoryImpl — typed to access raw credential lookup
        username: Username or email to authenticate
        password: Plain text password

    Returns:
        UserEntity if authentication successful, None otherwise
    """
    # Try username first, then fall back to email
    user_entity = await repository.get_by_username(username)

    if not user_entity:
        user_entity = await repository.get_by_email(username)

    if not user_entity:
        return None

    # Retrieve hashed_password from the raw document (infra-level detail)
    hashed_password = await repository.get_hashed_password(user_entity.username)

    if hashed_password is None:
        return None

    if not verify_password(password, hashed_password):
        return None

    if not user_entity.is_active:
        return None

    return user_entity
