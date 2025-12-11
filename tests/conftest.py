"""
Test configuration and fixtures
"""
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
import os
from typing import AsyncGenerator
from unittest.mock import AsyncMock, patch

# Set test environment variables
os.environ['DATABASE_URL'] = 'mongodb://localhost:27017/test_db'
os.environ['TYPE_DB'] = 'mongo'

from main import app


@pytest.fixture
def client():
    """Synchronous test client"""
    return TestClient(app)


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Asynchronous test client"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def authenticated_client(mock_user) -> AsyncGenerator[AsyncClient, None]:
    """
    Asynchronous test client with authentication automatically mocked
    Use this for endpoint tests that require authentication
    """
    with patch('auth.service.get_user_by_id', new_callable=AsyncMock) as mock_get_user:
        mock_get_user.return_value = mock_user
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac


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




# JWT Authentication fixtures
@pytest.fixture
def mock_user():
    """Mock authenticated user"""
    from models.user import UserInDB
    from datetime import datetime
    from bson import ObjectId
    
    return UserInDB(
        id=str(ObjectId()),
        username="testuser",
        email="test@example.com",
        hashed_password="$2b$12$fake_hash",
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@pytest.fixture
def valid_jwt_token(mock_user):
    """Generate a valid JWT token for testing"""
    from auth.jwt import create_access_token
    
    token_data = {
        "sub": mock_user.username,
        "user_id": str(mock_user.id)  # Ensure id is string for JSON serialization
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

