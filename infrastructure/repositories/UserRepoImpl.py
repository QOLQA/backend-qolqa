from __future__ import annotations

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from application.dtos.auth.AuthRequest import UserCreateRequest, UserUpdateRequest, AdminUserUpdateRequest
from domain.entities.auth.UserEntity import UserEntity
from domain.enums.AuthProviderEnum import AuthProviderEnum
from domain.errors import Duplicate, Missing, InvalidCredentials, PasswordRequiredForLocalLogin
from domain.repositories.user.repo import IUserRepository
from domain.security.password import IPasswordHasher
from infrastructure.mappers import UserMapper
from infrastructure.security.bcrypt_hasher import BcryptHasher


class UserRepositoryImpl(IUserRepository[UserEntity, UserCreateRequest, UserUpdateRequest]):
    """MongoDB implementation of IUserRepository.

    All DB operations use UserMapper — zero inline mapping.
    All domain errors are raised as Missing/Duplicate, never HTTPException.
    Password hashing is delegated to injected IPasswordHasher.
    """

    def __init__(
        self,
        database: AsyncIOMotorDatabase,
        hasher: IPasswordHasher | None = None,
    ) -> None:
        self.collection = database['users']
        self._hasher = hasher or BcryptHasher()

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

    async def verify_credentials(self, username: str, password: str) -> UserEntity:
        """Verify user credentials by username or email and password.

        Uses injected IPasswordHasher for verification.
        """
        # Try username first, then fall back to email
        user_entity = await self.get_by_username(username)

        if not user_entity:
            user_entity = await self.get_by_email(username)

        if not user_entity:
            raise InvalidCredentials()

        # Retrieve hashed_password from the raw document
        hashed_password = await self.get_hashed_password(user_entity.username)

        # Guard: Google-only account has no password — cannot log in via /login
        if (
            user_entity.auth_provider == AuthProviderEnum.google
            and user_entity.is_active
            and hashed_password is None
        ):
            raise PasswordRequiredForLocalLogin()

        if hashed_password is None or not self._hasher.verify(password, hashed_password):
            raise InvalidCredentials()

        if not user_entity.is_active:
            raise InvalidCredentials()

        return user_entity

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
        hashed_password = self._hasher.hash(entity_create.password)

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
    # Google Auth                                                          #
    # ------------------------------------------------------------------ #

    async def get_by_google_id(self, google_id: str) -> UserEntity | None:
        """Retrieve a user by google_id. Returns None if not found."""
        raw = await self.collection.find_one({'google_id': google_id})
        if raw is None:
            return None
        return UserMapper.to_entity(raw)

    async def link_google_account(self, user_id: str, google_id: str) -> UserEntity:
        """Link a Google account to an existing user.

        Only sets google_id — never touches token_version, auth_provider, or hashed_password.
        """
        if not ObjectId.is_valid(str(user_id)):
            raise Missing(msg=f'Invalid user id format: {user_id}')

        # Verify user exists
        existing = await self.collection.find_one({'_id': ObjectId(str(user_id))})
        if existing is None:
            raise Missing(msg=f'User with id {user_id} not found')

        try:
            result = await self.collection.update_one(
                {'_id': ObjectId(str(user_id))},
                {'$set': {'google_id': google_id}},
            )
        except Exception as exc:
            from pymongo.errors import DuplicateKeyError
            if isinstance(exc, DuplicateKeyError):
                raise Duplicate(msg='google_id already linked')
            raise

        if result.matched_count == 0:
            raise Missing(msg=f'User with id {user_id} not found')

        return await self.get_by_id(user_id)

    async def add_google_user(
        self,
        username: str,
        email: str,
        full_name: str | None,
        google_id: str,
        profile_picture_url: str | None,
    ) -> UserEntity:
        """Create a new Google-authenticated user (no password, no hashing)."""
        # Duplicate checks
        existing_username = await self.get_by_username(username)
        if existing_username:
            raise Duplicate(msg=f'Username {username} already exists')

        existing_email = await self.get_by_email(email)
        if existing_email:
            raise Duplicate(msg=f'Email {email} already exists')

        # Build insertable document via mapper
        doc = UserMapper.from_google_request(username, email, full_name, google_id, profile_picture_url)

        try:
            result = await self.collection.insert_one(doc)
        except Exception as exc:
            from pymongo.errors import DuplicateKeyError
            if isinstance(exc, DuplicateKeyError):
                raise Duplicate(msg=f'Google user with google_id {google_id} already exists')
            raise

        return await self.get_by_id(str(result.inserted_id))
