from __future__ import annotations

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from application.dtos.auth.AuthRequest import UserCreateRequest, UserUpdateRequest, AdminUserUpdateRequest
from infrastructure.password import get_password_hash
from domain.entities.auth.UserEntity import UserEntity
from domain.errors import Duplicate, Missing
from domain.repositories.user.repo import IUserRepository
from infrastructure.mappers import UserMapper


class UserRepositoryImpl(IUserRepository[UserEntity, UserCreateRequest, UserUpdateRequest]):
    """MongoDB implementation of IUserRepository.

    All DB operations use UserMapper — zero inline mapping.
    All domain errors are raised as Missing/Duplicate, never HTTPException.
    Password hashing is handled internally in add().
    """

    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        self.collection = database['users']

    # ------------------------------------------------------------------ #
    # Read                                                                 #
    # ------------------------------------------------------------------ #

    async def get_by_id(self, id: str) -> UserEntity:
        """Retrieve a user by its string ObjectId."""
        if not ObjectId.is_valid(str(id)):
            raise Missing(msg=f'Invalid user id format: {id}')

        raw = await self.collection.find_one({'_id': ObjectId(str(id))})

        if raw is None:
            raise Missing(msg=f'User with id {id} not found')

        return UserMapper.to_entity(raw)

    async def get_all(self) -> list[UserEntity]:
        """Retrieve all users."""
        cursor = self.collection.find()
        raws = await cursor.to_list(length=None)
        return [UserMapper.to_entity(raw) for raw in raws]

    async def get_by_username(self, username: str) -> UserEntity | None:
        """Retrieve a user by username. Returns None if not found."""
        raw = await self.collection.find_one({'username': username.lower()})

        if raw is None:
            return None

        return UserMapper.to_entity(raw)

    async def get_by_email(self, email: str) -> UserEntity | None:
        """Retrieve a user by email. Returns None if not found."""
        raw = await self.collection.find_one({'email': email.lower()})

        if raw is None:
            return None

        return UserMapper.to_entity(raw)

    async def get_hashed_password(self, username: str) -> str | None:
        """Return only the hashed_password field for credential verification.

        This is an auth-specific infrastructure helper — not part of IUserRepository.
        It avoids exposing hashed_password on UserEntity (domain purity).
        """
        raw = await self.collection.find_one(
            {'username': username.lower()},
            {'hashed_password': 1},
        )
        if raw is None:
            return None
        return raw.get('hashed_password')

    # ------------------------------------------------------------------ #
    # Write                                                                #
    # ------------------------------------------------------------------ #

    async def add(self, entity_create: UserCreateRequest) -> UserEntity:
        """Create a new user after checking for duplicate username/email.

        Hashes the password internally — callers must NOT pre-hash.
        """
        # Duplicate checks
        existing_username = await self.get_by_username(entity_create.username)
        if existing_username:
            raise Duplicate(msg=f'Username {entity_create.username} already exists')

        existing_email = await self.get_by_email(entity_create.email)
        if existing_email:
            raise Duplicate(msg=f'Email {entity_create.email} already exists')

        # Hash password before storage
        hashed_password = get_password_hash(entity_create.password)

        # Build insertable document via mapper
        doc = UserMapper.from_create_request(entity_create, hashed_password)

        result = await self.collection.insert_one(doc)

        return await self.get_by_id(str(result.inserted_id))

    async def update(self, id: str, entity_update: UserUpdateRequest | AdminUserUpdateRequest) -> UserEntity:
        """Partially update a user. Returns the updated entity."""
        if not ObjectId.is_valid(str(id)):
            raise Missing(msg=f'Invalid user id format: {id}')

        # Verify exists
        await self.get_by_id(id)

        update_data = entity_update.model_dump(exclude_unset=True, mode='json')
        if not update_data:
            return await self.get_by_id(id)

        result = await self.collection.update_one(
            {'_id': ObjectId(str(id))},
            {'$set': update_data},
        )

        if result.matched_count == 0:
            raise Missing(msg=f'User with id {id} not found')

        return await self.get_by_id(id)

    async def delete(self, id: str) -> None:
        """Delete a user by id."""
        if not ObjectId.is_valid(str(id)):
            raise Missing(msg=f'Invalid user id format: {id}')

        result = await self.collection.delete_one({'_id': ObjectId(str(id))})

        if result.deleted_count == 0:
            raise Missing(msg=f'User with id {id} not found')

    # ------------------------------------------------------------------ #
    # Google Auth (stubs — full implementation in WU2)                    #
    # ------------------------------------------------------------------ #

    async def get_by_google_id(self, google_id: str) -> UserEntity | None:
        """Retrieve a user by google_id. Returns None if not found."""
        raw = await self.collection.find_one({'google_id': google_id})
        if raw is None:
            return None
        return UserMapper.to_entity(raw)

    async def link_google_account(self, user_id: str, google_id: str) -> UserEntity:
        """Link a Google account to an existing user."""
        raise NotImplementedError("Full implementation in WU2")

    async def add_google_user(
        self,
        username: str,
        email: str,
        full_name: str | None,
        google_id: str,
        profile_picture_url: str | None,
    ) -> UserEntity:
        """Create a new Google-authenticated user (no password)."""
        raise NotImplementedError("Full implementation in WU2")
