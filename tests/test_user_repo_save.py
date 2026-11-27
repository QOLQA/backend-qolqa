"""Tests for UserRepositoryImpl.save() upsert behavior and duplicate-key translation.

Pins the fix for the register 500: a DuplicateKeyError raised by any unique
index (username, email, or google_id) must surface as the domain Duplicate
error, which the global handler maps to 409 — never as an unhandled 500.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from domain.entities.auth.UserEntity import UserEntity
from domain.errors import Duplicate
from infra.persistence.repositories import UserRepositoryImpl


def _new_local_entity() -> UserEntity:
    """New local user: empty id, google_id None (the register /auth/register case)."""
    return UserEntity.create_local(
        id='',
        username='newuser',
        email='new@example.com',
        full_name='New User',
    )


def _raw_doc(oid: ObjectId) -> dict:
    return {
        '_id': oid,
        'username': 'newuser',
        'email': 'new@example.com',
        'full_name': 'New User',
        'is_active': True,
        'created_at': datetime.now(UTC),
        'roles': ['user'],
        'token_version': 0,
        'google_id': None,
        'auth_provider': 'local',
    }


def _mock_db(collection: AsyncMock) -> MagicMock:
    mock_db = MagicMock()
    mock_db.__getitem__ = MagicMock(return_value=collection)
    return mock_db


class TestUserRepoSaveUpsert:
    """save() keeps its upsert contract for new local users."""

    @pytest.mark.asyncio
    async def test_save_new_user_success_upsert(self):
        mock_collection = AsyncMock()
        # find_one sequence: username check (None), email check (None), re-fetch (doc)
        oid = ObjectId()
        mock_collection.find_one = AsyncMock(
            side_effect=[None, None, _raw_doc(oid)]
        )

        repo = UserRepositoryImpl(_mock_db(mock_collection))
        entity = await repo.save(_new_local_entity())

        assert entity.id == str(oid)
        assert entity.username == 'newuser'
        assert entity.google_id is None

        # Upsert by username filter for new users (no valid id yet)
        mock_collection.update_one.assert_awaited_once()
        args, kwargs = mock_collection.update_one.await_args
        assert args[0] == {'username': 'newuser'}
        assert kwargs['upsert'] is True


class TestUserRepoSaveDuplicateKeyTranslation:
    """A unique-index violation in save() becomes the domain Duplicate error."""

    @pytest.mark.asyncio
    async def test_save_google_id_null_collision_raises_duplicate(self):
        """The production failure: second local user hits google_id_1 dup key { google_id: null }."""
        mock_collection = AsyncMock()
        mock_collection.find_one = AsyncMock(side_effect=[None, None])
        mock_collection.update_one = AsyncMock(
            side_effect=DuplicateKeyError(
                'E11000 duplicate key error collection: qolqa.users '
                'index: google_id_1 dup key: { google_id: null }',
                11000,
                {'index': 0, 'code': 11000, 'keyPattern': {'google_id': 1}, 'keyValue': {'google_id': None}},
            )
        )

        repo = UserRepositoryImpl(_mock_db(mock_collection))
        with pytest.raises(Duplicate) as excinfo:
            await repo.save(_new_local_entity())

        assert 'google_id' in excinfo.value.msg

    @pytest.mark.asyncio
    async def test_save_username_index_collision_raises_duplicate(self):
        mock_collection = AsyncMock()
        mock_collection.find_one = AsyncMock(side_effect=[None, None])
        mock_collection.update_one = AsyncMock(
            side_effect=DuplicateKeyError(
                'E11000 duplicate key error collection: qolqa.users '
                'index: username_1 dup key: { username: "newuser" }',
                11000,
                {'index': 0, 'code': 11000, 'keyPattern': {'username': 1}, 'keyValue': {'username': 'newuser'}},
            )
        )

        repo = UserRepositoryImpl(_mock_db(mock_collection))
        with pytest.raises(Duplicate) as excinfo:
            await repo.save(_new_local_entity())

        assert 'username' in excinfo.value.msg

    @pytest.mark.asyncio
    async def test_save_duplicate_key_without_details_raises_duplicate(self):
        """Defensive: a malformed DuplicateKeyError still becomes Duplicate, never a 500."""
        mock_collection = AsyncMock()
        mock_collection.find_one = AsyncMock(side_effect=[None, None])
        mock_collection.update_one = AsyncMock(side_effect=DuplicateKeyError('dup', 11000))

        repo = UserRepositoryImpl(_mock_db(mock_collection))
        with pytest.raises(Duplicate):
            await repo.save(_new_local_entity())
