from domain.entities.auth.UserEntity import UserEntity
from domain.errors import InvalidCredentials, PasswordRequiredForLocalLogin
from domain.repositories.user.repo import IUserRepository


async def authenticate_user(
    repository: IUserRepository,
    username: str,
    password: str,
) -> UserEntity:
    """
    Authenticate a user by username or email and password.

    Args:
        repository: IUserRepository — uses verify_credentials for auth
        username: Username or email to authenticate
        password: Plain text password

    Returns:
        UserEntity if authentication successful

    Raises:
        InvalidCredentials: If username/password combination is invalid or user is inactive
        PasswordRequiredForLocalLogin: If user has no local password (Google-only account)
    """
    return await repository.verify_credentials(username, password)
