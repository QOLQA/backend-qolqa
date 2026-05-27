"""
Admin controller.
Handles user management operations restricted to admin role.
"""
from typing import List

from bson import ObjectId
from fastapi import APIRouter, Depends, status

from application.dtos.auth.AuthRequest import AdminUserUpdateRequest
from application.dtos.auth.AuthResponse import UserResponse
from domain.entities.auth.UserEntity import UserEntity
from domain.enums.RoleEnum import RoleEnum
from infrastructure.mappers import UserMapper
from infrastructure.repositories.UserRepoImpl import UserRepositoryImpl
from api.dependencies.auth import require_admin, get_user_repository
from api.handle_errors import handle_common_errors

router = APIRouter()


@router.get('/users', response_model=List[UserResponse])
async def list_users(
    _: UserEntity = Depends(require_admin),
    repository: UserRepositoryImpl = Depends(get_user_repository),
) -> List[UserResponse]:
    """List all users. Admin only."""
    try:
        users = await repository.get_all()
        return [UserMapper.to_response(u) for u in users]
    except Exception as exc:
        await handle_common_errors(exc)


@router.get('/users/{user_id}', response_model=UserResponse)
async def get_user(
    user_id: str,
    _: UserEntity = Depends(require_admin),
    repository: UserRepositoryImpl = Depends(get_user_repository),
) -> UserResponse:
    """Get a user by ID. Admin only."""
    try:
        user = await repository.get_by_id(user_id)
        return UserMapper.to_response(user)
    except Exception as exc:
        await handle_common_errors(exc)


@router.patch('/users/{user_id}', response_model=UserResponse)
async def update_user(
    user_id: str,
    user_update: AdminUserUpdateRequest,
    _: UserEntity = Depends(require_admin),
    repository: UserRepositoryImpl = Depends(get_user_repository),
) -> UserResponse:
    """Update any user. Admin only. Changing roles invalidates existing tokens."""
    try:
        updated = await repository.update(user_id, user_update)
        # If roles changed, invalidate all existing tokens for this user
        if user_update.roles is not None:
            await repository.collection.update_one(
                {'_id': ObjectId(user_id)},
                {'$inc': {'token_version': 1}},
            )
            # Re-fetch to get updated token_version
            updated = await repository.get_by_id(user_id)
        return UserMapper.to_response(updated)
    except Exception as exc:
        await handle_common_errors(exc)


@router.delete('/users/{user_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    _: UserEntity = Depends(require_admin),
    repository: UserRepositoryImpl = Depends(get_user_repository),
) -> None:
    """Hard delete a user. Admin only."""
    try:
        await repository.delete(user_id)
    except Exception as exc:
        await handle_common_errors(exc)


@router.post('/users/{user_id}/promote', response_model=UserResponse)
async def promote_user_to_admin(
    user_id: str,
    _: UserEntity = Depends(require_admin),
    repository: UserRepositoryImpl = Depends(get_user_repository),
) -> UserResponse:
    """
    Promote a user to admin role.
    Adds RoleEnum.admin to the user's roles list (keeps existing roles).
    Increments token_version to invalidate current tokens — user must re-login.
    Admin only.
    """
    try:
        user = await repository.get_by_id(user_id)

        if RoleEnum.admin in user.roles:
            # Already admin — return current state without side effects
            return UserMapper.to_response(user)

        # Add admin to the existing roles list (preserves [user, ...])
        new_roles = list(user.roles) + [RoleEnum.admin]

        # Update roles via repository (respects layer boundary).
        # Serialize enum values so MongoDB receives plain strings.
        await repository.update(
            user_id,
            AdminUserUpdateRequest(roles=new_roles),
        )

        # Atomically increment token_version to invalidate existing tokens.
        # Allowed per AGENTS.md: targeted $inc for token_version in admin controller.
        await repository.collection.update_one(
            {'_id': ObjectId(user_id)},
            {'$inc': {'token_version': 1}},
        )

        updated = await repository.get_by_id(user_id)
        return UserMapper.to_response(updated)

    except Exception as exc:
        await handle_common_errors(exc)
