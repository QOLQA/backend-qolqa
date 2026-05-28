"""
Test configuration and fixtures
"""
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
import os
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

# Set test environment variables
os.environ['DATABASE_URL'] = 'mongodb://localhost:27017/test_db'
os.environ['TYPE_DB'] = 'mongo'

from main import app
from infrastructure.db_factory import get_database


def get_mock_database() -> MagicMock:
    """Returns a MagicMock that mimics AsyncIOMotorDatabase."""
    mock_collection = AsyncMock()
    mock_collection.find_one = AsyncMock(return_value=None)
    mock_collection.find = MagicMock(return_value=AsyncMock())
    mock_collection.insert_one = AsyncMock()
    mock_collection.update_one = AsyncMock()
    mock_collection.delete_one = AsyncMock()
    mock_collection.delete_many = AsyncMock()

    # cursor mock for find()
    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=[])
    mock_collection.find = MagicMock(return_value=mock_cursor)

    mock_db = MagicMock()
    mock_db.__getitem__ = MagicMock(return_value=mock_collection)
    return mock_db


async def override_get_database() -> AsyncGenerator[MagicMock, None]:
    """FastAPI dependency override — yields a mock DB instead of real MongoDB."""
    yield get_mock_database()


@pytest.fixture
def client():
    """Synchronous test client"""
    return TestClient(app)


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Asynchronous test client with mocked DB"""
    app.dependency_overrides[get_database] = override_get_database
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def authenticated_client(mock_user) -> AsyncGenerator[AsyncClient, None]:
    """
    Asynchronous test client with authentication automatically mocked.
    Overrides get_current_user dependency so tests bypass JWT + DB validation.
    """
    from domain.entities.auth.UserEntity import UserEntity
    from api.dependencies.auth import get_current_user

    mock_entity = UserEntity(
        id=str(mock_user.id),
        username=mock_user.username,
        email=mock_user.email,
        full_name=mock_user.full_name,
        is_active=mock_user.is_active,
        created_at=mock_user.created_at,
        token_version=0,
        roles=[],
    )

    async def override_get_current_user():
        return mock_entity

    app.dependency_overrides[get_database] = override_get_database
    app.dependency_overrides[get_current_user] = override_get_current_user
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def mock_solution_data(mock_user):
    """Mock data for solution creation"""
    return {
        "name": "Test Solution",
        "last_version_saved": "unknown",
        "src_img": "http://test.com/image.png",
        "queries": [
            {
                "id": "query1",
                "full_query": "SELECT * FROM users",
                "collections": ["users"]
            }
        ]
        # user_id is added by the endpoint from current_user
    }


@pytest.fixture
def mock_version_data():
    """Mock data for version creation"""
    return {
        "submodels": [
            {
                "nodes": [
                    {
                        "id": "node1",
                        "name": "User",
                        "type": "entity",
                        "position": {"x": 100, "y": 100},
                        "cols": [
                            {
                                "id": "col1",
                                "name": "id",
                                "type": "int"
                            }
                        ],
                        "nested_nodes": None
                    }
                ],
                "edges": []
            }
        ],
        "description": "Test version",
        "solution_id": "test_solution_id"
    }


@pytest.fixture
def mock_invalid_solution_data():
    """Mock invalid solution data for validation tests"""
    return {
        "last_version_saved": "unknown",
        "src_img": "http://test.com/image.png",
        "queries": []
        # Missing required field: name
    }


@pytest.fixture
def mock_partial_update_data():
    """Mock data for partial updates"""
    return {
        "name": "Updated Solution Name"
    }




import types as _types

# JWT Authentication fixtures
@pytest.fixture
def mock_user() -> _types.SimpleNamespace:
    """Mock authenticated user"""
    import types
    from datetime import datetime
    from bson import ObjectId

    user = types.SimpleNamespace(
        id=str(ObjectId()),
        username="testuser",
        email="test@example.com",
        full_name=None,
        is_active=True,
        roles=[],
        token_version=0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    return user


@pytest.fixture
def valid_jwt_token(mock_user):
    """Generate a valid JWT token for testing"""
    from infrastructure.jwt import create_access_token

    token_data = {
        "sub": mock_user.username,
        "user_id": str(mock_user.id),
        "roles": [],
        "token_version": 0,
    }
    return create_access_token(token_data)


@pytest.fixture
def auth_headers(valid_jwt_token):
    """Authorization headers with valid JWT token"""
    return {
        "Authorization": f"Bearer {valid_jwt_token}"
    }


# Future JWT fixtures
@pytest.fixture
def mock_user_credentials():
    """Mock user credentials for future JWT tests"""
    return {
        "username": "testuser",
        "password": "testpassword123"
    }


@pytest.fixture
def mock_jwt_token():
    """Mock JWT token for future authentication tests"""
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test.token"

