from application.dtos.auth.AuthRequest import UserCreateRequest
from domain.entities.auth.UserEntity import UserEntity
from infrastructure.repositories.UserRepoImpl import UserRepositoryImpl


async def register_user(
    repository: UserRepositoryImpl,
    user_create: UserCreateRequest,
) -> UserEntity:
    """
    Register a new user.

    Args:
        repository: UserRepositoryImpl — handles duplicate checks and password hashing
        user_create: UserCreateRequest DTO with validated user data

    Returns:
        UserEntity representing the newly created user
    """
    return await repository.add(user_create)
