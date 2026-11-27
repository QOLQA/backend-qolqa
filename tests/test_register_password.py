"""Tests pinning the register-then-login bug.

RegisterUser dropped command.password and UserRepositoryImpl.save() persisted
documents without hashed_password, so a freshly registered user always got
InvalidCredentials (401) on the immediate login. These tests pin that the
register flow hashes and persists the password via the repository port.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from bson import ObjectId

from application.dtos.auth.commands import RegisterCommand
from application.use_cases.auth.RegisterUser import register_user
from domain.errors import Duplicate
from domain.security.password import IPasswordHasher
from infra.persistence.repositories import UserRepositoryImpl


class FakeHasher(IPasswordHasher):
    """Deterministic hasher — keeps tests fast and asserts the plain password."""

    def __init__(self) -> None:
        self.hashed: list[str] = []

    def hash(self, password: str) -> str:
        self.hashed.append(password)
        return f'hashed({password})'

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        return hashed_password == f'hashed({plain_password})'


def _raw_doc(oid: ObjectId, username: str = 'juan3', email: str = 'juan3@example.com') -> dict:
    return {
        '_id': oid,
        'username': username,
        'email': email,
        'full_name': 'Juan Three',
        'is_active': True,
        'created_at': datetime.now(UTC),
        'roles': ['user'],
        'token_version': 0,
        'hashed_password': 'hashed(Secret123)',
        'google_id': None,
        'auth_provider': 'local',
    }


def _mock_db(collection: AsyncMock) -> MagicMock:
    mock_db = MagicMock()
    mock_db.__getitem__ = MagicMock(return_value=collection)
    return mock_db


class TestRegisterUserUseCase:
    """register_user must delegate creation (with the password) to the repo port."""

    @pytest.mark.asyncio
    async def test_register_user_passes_password_to_add_local_user(self):
        mock_repo = AsyncMock()
        created = MagicMock()
        mock_repo.add_local_user = AsyncMock(return_value=created)

        command = RegisterCommand(
            username='juan3',
            email='juan3@example.com',
            password='Secret123',
            full_name='Juan Three',
        )

        entity = await register_user(mock_repo, command)

        assert entity is created
        mock_repo.add_local_user.assert_awaited_once_with(
            username='juan3',
            email='juan3@example.com',
            full_name='Juan Three',
            password='Secret123',
        )
        mock_repo.save.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_register_user_rejects_empty_username(self):
        mock_repo = AsyncMock()
        command = RegisterCommand(username='  ', email='a@b.com', password='Secret123')

        with pytest.raises(ValueError):
            await register_user(mock_repo, command)
        mock_repo.add_local_user.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_register_user_rejects_empty_email(self):
        mock_repo = AsyncMock()
        command = RegisterCommand(username='juan3', email='', password='Secret123')

        with pytest.raises(ValueError):
            await register_user(mock_repo, command)
        mock_repo.add_local_user.assert_not_awaited()


class TestUserRepoAddLocalUser:
    """Repository persists a hashed password for local registration."""

    @pytest.mark.asyncio
    async def test_add_local_user_hashes_and_persists_password(self):
        mock_collection = AsyncMock()
        oid = ObjectId()
        # find_one sequence: username check (None), email check (None), get_by_id (doc)
        mock_collection.find_one = AsyncMock(side_effect=[None, None, _raw_doc(oid)])
        mock_collection.insert_one = AsyncMock(return_value=MagicMock(inserted_id=oid))

        hasher = FakeHasher()
        repo = UserRepositoryImpl(_mock_db(mock_collection), hasher=hasher)

        entity = await repo.add_local_user('juan3', 'juan3@example.com', 'Juan Three', 'Secret123')

        assert entity.id == str(oid)
        assert entity.username == 'juan3'

        # The plain password was hashed exactly once and persisted
        assert hasher.hashed == ['Secret123']
        mock_collection.insert_one.assert_awaited_once()
        doc = mock_collection.insert_one.await_args.args[0]
        assert doc['hashed_password'] == 'hashed(Secret123)'
        assert doc['username'] == 'juan3'
        assert doc['email'] == 'juan3@example.com'
        assert doc['auth_provider'] == 'local'

    @pytest.mark.asyncio
    async def test_add_local_user_duplicate_username(self):
        mock_collection = AsyncMock()
        oid = ObjectId()
        mock_collection.find_one = AsyncMock(side_effect=[_raw_doc(oid)])

        repo = UserRepositoryImpl(_mock_db(mock_collection), hasher=FakeHasher())
        with pytest.raises(Duplicate):
            await repo.add_local_user('juan3', 'juan3@example.com', None, 'Secret123')
        mock_collection.insert_one.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_add_local_user_duplicate_email(self):
        mock_collection = AsyncMock()
        oid = ObjectId()
        mock_collection.find_one = AsyncMock(side_effect=[None, _raw_doc(oid)])

        repo = UserRepositoryImpl(_mock_db(mock_collection), hasher=FakeHasher())
        with pytest.raises(Duplicate):
            await repo.add_local_user('juan3', 'juan3@example.com', None, 'Secret123')
        mock_collection.insert_one.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_add_local_user_race_insert_raises_duplicate(self):
        from pymongo.errors import DuplicateKeyError

        mock_collection = AsyncMock()
        mock_collection.find_one = AsyncMock(side_effect=[None, None])
        mock_collection.insert_one = AsyncMock(
            side_effect=DuplicateKeyError(
                'E11000 duplicate key error collection: qolqa.users index: username_1',
                11000,
                {'keyPattern': {'username': 1}},
            )
        )

        repo = UserRepositoryImpl(_mock_db(mock_collection), hasher=FakeHasher())
        with pytest.raises(Duplicate):
            await repo.add_local_user('juan3', 'juan3@example.com', None, 'Secret123')
