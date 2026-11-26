"""
Admin controller.
Handles user management operations restricted to admin role.
"""

from bson import ObjectId
from fastapi import APIRouter, status

from domain.enums.RoleEnum import RoleEnum
from infra.persistence.mappers import UserMapper
from infra.presentation.dependencies import AdminUserDep, UserRepoDep
from infra.presentation.dtos.auth.request import AdminUserUpdateRequest
from infra.presentation.dtos.auth.response import UserResponse

router = APIRouter()


@router.get('/users', response_model=list[UserResponse])
async def list_users(
    _: AdminUserDep,
    repository: UserRepoDep,
) -> list[UserResponse]:
    """List all users. Admin only."""
    users = await repository.get_all()
    return [UserMapper.to_response(u) for u in users]


@router.get('/users/{user_id}', response_model=UserResponse)
async def get_user(
    user_id: str,
    _: AdminUserDep,
    repository: UserRepoDep,
) -> UserResponse:
    """Get a user by ID. Admin only."""
    user = await repository.get_by_id(user_id)
    return UserMapper.to_response(user)


@router.patch('/users/{user_id}', response_model=UserResponse)
async def update_user(
    user_id: str,
    user_update: AdminUserUpdateRequest,
    _: AdminUserDep,
    repository: UserRepoDep,
) -> UserResponse:
    """Update any user. Admin only. Changing roles invalidates existing tokens."""
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


@router.delete('/users/{user_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    _: AdminUserDep,
    repository: UserRepoDep,
) -> None:
    """Hard delete a user. Admin only."""
    await repository.delete(user_id)


@router.post('/users/{user_id}/promote', response_model=UserResponse)
async def promote_user_to_admin(
    user_id: str,
    _: AdminUserDep,
    repository: UserRepoDep,
) -> UserResponse:
    """
    Promote a user to admin role.
    Adds RoleEnum.admin to the user's roles list (keeps existing roles).
    Increments token_version to invalidate current tokens — user must re-login.
    Admin only.
    """
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

