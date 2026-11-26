"""
User self-service controller.
Handles profile update and account deletion for the authenticated user.
"""
from fastapi import APIRouter, status

from infra.persistence.mappers import UserMapper
from infra.presentation.dependencies import CurrentUserDep, UserRepoDep
from infra.presentation.dtos.auth.request import UserUpdateRequest
from infra.presentation.dtos.auth.response import UserResponse

router = APIRouter()


@router.patch('/me', response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdateRequest,
    current_user: CurrentUserDep,
    repository: UserRepoDep,
) -> UserResponse:
    """Update the authenticated user's own profile."""
    updated = await repository.update(current_user.id, user_update)
    return UserMapper.to_response(updated)


@router.delete('/me', status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_user(
    current_user: CurrentUserDep,
    repository: UserRepoDep,
) -> None:
    """Delete the authenticated user's own account."""
    await repository.delete(current_user.id)
