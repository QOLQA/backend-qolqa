from domain.entities.auth.UserEntity import UserEntity
from application.repositories.user.repo import IUserRepository


async def get_user_by_id(
    repository: IUserRepository,
    user_id: str,
) -> UserEntity:
    """
    Fetch a user by their ID.

    Args:
        repository: IUserRepository implementation
        user_id: String ObjectId of the user

    Returns:
        UserEntity for the found user

    Raises:
        Missing: If no user with that id exists
    """
    return await repository.get_by_id(user_id)
