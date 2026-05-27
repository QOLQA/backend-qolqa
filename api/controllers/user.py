"""
User self-service controller.
Handles profile update and account deletion for the authenticated user.
"""
from fastapi import APIRouter, Depends, status

from application.dtos.auth.AuthRequest import UserUpdateRequest
from application.dtos.auth.AuthResponse import UserResponse
from domain.entities.auth.UserEntity import UserEntity
from infrastructure.mappers import UserMapper
from infrastructure.repositories.UserRepoImpl import UserRepositoryImpl
from api.dependencies.auth import get_current_user, get_user_repository
from api.handle_errors import handle_common_errors

router = APIRouter()


@router.patch('/me', response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdateRequest,
    current_user: UserEntity = Depends(get_current_user),
    repository: UserRepositoryImpl = Depends(get_user_repository),
) -> UserResponse:
    """Update the authenticated user's own profile."""
    try:
        updated = await repository.update(current_user.id, user_update)
        return UserMapper.to_response(updated)
    except Exception as exc:
        await handle_common_errors(exc)


@router.delete('/me', status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_user(
    current_user: UserEntity = Depends(get_current_user),
    repository: UserRepositoryImpl = Depends(get_user_repository),
) -> None:
    """Delete the authenticated user's own account."""
    try:
        await repository.delete(current_user.id)
    except Exception as exc:
        await handle_common_errors(exc)
