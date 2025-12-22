"""
Authentication tests for JWT implementation
"""
import pytest
from fastapi import status
from unittest.mock import AsyncMock, patch


@pytest.mark.auth
class TestJWTAuthentication:
    """Test suite for JWT authentication"""
    
    @pytest.mark.asyncio
    async def test_login_success(self, async_client):
        """Test successful user login and JWT token generation"""
        # Mock user authentication
        with patch('auth.service.authenticate_user', new_callable=AsyncMock) as mock_auth, \
             patch('auth.service.create_user_token', new_callable=AsyncMock) as mock_token:
            
            from models.user import UserInDB
            from bson import ObjectId
            from datetime import datetime
            
            mock_user = UserInDB(
                _id=ObjectId(),
                username="testuser",
                email="test@example.com",
                hashed_password="hashed",
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            mock_auth.return_value = mock_user
            mock_token.return_value = {
                "access_token": "fake_token",
                "token_type": "bearer"
            }
            
            response = await async_client.post(
                "/auth/login",
                data={"username": "testuser", "password": "secret"}
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "access_token" in data
            assert "token_type" in data
            assert data["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, async_client):
        """Test login with invalid credentials"""
        with patch('auth.service.authenticate_user', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = None
            
            response = await async_client.post(
                "/auth/login",
                data={"username": "nonexistent", "password": "wrongpassword"}
            )
            
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    async def test_login_missing_credentials(self, async_client):
        """Test login with missing credentials"""
        response = await async_client.post("/auth/login", data={})
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @pytest.mark.asyncio
    async def test_access_protected_endpoint_with_valid_token(self, async_client):
        """Test accessing protected endpoint with valid token"""
        from auth.jwt import create_access_token
        from auth.repository import UserRepository
        from models.user import UserInDB, UserCreate
        from datetime import datetime
        from bson import ObjectId
        
        # Create valid ObjectId for user
        user_id = str(ObjectId())
        
        # Create a valid JWT token
        token_data = {
            "sub": "testuser",
            "user_id": user_id
        }
        valid_token = create_access_token(token_data)
        
        # Mock database operations
        with patch('auth.service.get_user_by_id', new_callable=AsyncMock) as mock_get_user, \
             patch('solution.service.get_all', new_callable=AsyncMock) as mock_get_all:
            
            # Mock the user retrieval
            mock_user = UserInDB(
                id=user_id,
                username="testuser",
                email="test@example.com",
                hashed_password="fake_hash",
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            mock_get_user.return_value = mock_user
            
            # Mock empty solutions list for this user
            mock_get_all.return_value = []
            
            response = await async_client.get(
                "/solutions",
                headers={"Authorization": f"Bearer {valid_token}"}
            )
            
            assert response.status_code == status.HTTP_200_OK
            assert response.json() == []
    
    @pytest.mark.asyncio
    async def test_access_protected_endpoint_without_token(self, async_client):
        """Test accessing protected endpoint without token"""
        response = await async_client.get("/solutions")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    async def test_access_protected_endpoint_with_invalid_token(self, async_client):
        """Test accessing protected endpoint with invalid token"""
        response = await async_client.get(
            "/solutions",
            headers={"Authorization": "Bearer invalid.token.here"}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    async def test_token_expiration(self, async_client):
        """Test that expired tokens are rejected"""
        # Test with expired token
        from jose import jwt
        from datetime import datetime, timedelta
        from config.settings import settings
        
        expired_token = jwt.encode(
            {
                "sub": "testuser",
                "user_id": "123",
                "exp": datetime.utcnow() - timedelta(minutes=30)
            },
            settings.secret_key,
            algorithm=settings.algorithm
        )
        
        response = await async_client.get(
            "/solutions",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Refresh token not yet implemented")
    async def test_refresh_token(self, async_client, mock_jwt_token):
        """Test token refresh functionality"""
        response = await async_client.post(
            "/auth/refresh",
            headers={"Authorization": f"Bearer {mock_jwt_token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data


@pytest.mark.auth
class TestUserRegistration:
    """Test suite for user registration"""
    
    @pytest.mark.asyncio
    async def test_register_new_user_success(self, async_client):
        """Test successful user registration"""
        with patch('auth.service.register_user', new_callable=AsyncMock) as mock_register:
            from models.user import User
            from datetime import datetime
            
            mock_register.return_value = User(
                id="123",
                username="newuser",
                email="newuser@example.com",
                is_active=True,
                created_at=datetime.utcnow()
            )
            
            new_user = {
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "SecurePass123",
                "full_name": "New User"
            }
            
            response = await async_client.post("/auth/register", json=new_user)
            
            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["username"] == "newuser"
            assert "password" not in data  # Password should not be returned
            assert "hashed_password" not in data
    
    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, async_client):
        """Test registration with existing username"""
        with patch('auth.service.register_user', new_callable=AsyncMock) as mock_register:
            from utils.errors import Duplicate
            mock_register.side_effect = Duplicate(msg="Username already exists")
            
            user_data = {
                "username": "existinguser",
                "email": "new@example.com",
                "password": "SecurePass123"
            }
            
            response = await async_client.post("/auth/register", json=user_data)
            
            assert response.status_code == status.HTTP_409_CONFLICT
    
    @pytest.mark.asyncio
    async def test_register_weak_password(self, async_client):
        """Test registration with weak password"""
        weak_password_user = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "123"  # Too short/weak
        }
        
        response = await async_client.post("/auth/register", json=weak_password_user)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @pytest.mark.asyncio
    async def test_register_invalid_email(self, async_client):
        """Test registration with invalid email format"""
        invalid_email_user = {
            "username": "testuser",
            "email": "not-an-email",
            "password": "SecurePass123"
        }
        
        response = await async_client.post("/auth/register", json=invalid_email_user)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.auth
class TestJWTUtilities:
    """Test suite for JWT utility functions"""
    
    def test_create_access_token(self):
        """Test JWT token creation"""
        from auth.jwt import create_access_token
        
        token = create_access_token(data={"sub": "user123"})
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_decode_token_valid(self):
        """Test decoding valid JWT token"""
        from auth.jwt import create_access_token, decode_access_token
        
        token = create_access_token(data={"sub": "user123", "user_id": "456"})
        payload = decode_access_token(token)
        
        assert payload["sub"] == "user123"
        assert payload["user_id"] == "456"
        assert "exp" in payload
    
    def test_decode_token_invalid(self):
        """Test decoding invalid JWT token"""
        from auth.jwt import decode_access_token
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            decode_access_token("invalid.token.here")
        
        assert exc_info.value.status_code == 401
    
    def test_token_includes_expiration(self):
        """Test that generated tokens include expiration time"""
        from auth.jwt import create_access_token, decode_access_token
        
        token = create_access_token(data={"sub": "user123"})
        payload = decode_access_token(token)
        
        assert "exp" in payload
        assert "iat" in payload
        assert "type" in payload
        assert payload["type"] == "access"


@pytest.mark.auth
class TestPasswordHashing:
    """Test suite for password hashing utilities"""
    
    def test_hash_password(self):
        """Test password hashing"""
        from auth.password import get_password_hash
        
        hashed = get_password_hash("mypassword")
        
        assert hashed != "mypassword"
        assert len(hashed) > 0
        assert hashed.startswith("$2b$")  # bcrypt hash starts with $2b$
    
    def test_verify_password_correct(self):
        """Test password verification with correct password"""
        from auth.password import get_password_hash, verify_password
        
        password = "mypassword"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password"""
        from auth.password import get_password_hash, verify_password
        
        hashed = get_password_hash("mypassword")
        
        assert verify_password("wrongpassword", hashed) is False


@pytest.mark.auth
class TestAuthorizationRoles:
    """Test suite for role-based authorization (future feature)"""
    
    @pytest.mark.skip(reason="Role-based auth not yet implemented")
    @pytest.mark.asyncio
    async def test_admin_access_admin_endpoint(self, async_client):
        """Test admin user can access admin endpoints"""
        # TODO: Implement when roles are added
        pass
    
    @pytest.mark.skip(reason="Role-based auth not yet implemented")
    @pytest.mark.asyncio
    async def test_regular_user_denied_admin_endpoint(self, async_client):
        """Test regular user cannot access admin endpoints"""
        # TODO: Implement when roles are added
        pass
    
    @pytest.mark.asyncio
    async def test_user_can_only_modify_own_solutions(self, async_client):
        """Test users can only modify their own solutions"""
        from auth.jwt import create_access_token
        from models.solution import Solution
        from models.user import UserInDB
        from datetime import datetime
        from bson import ObjectId
        
        # Create valid ObjectIds
        user1_id = str(ObjectId())
        user2_id = str(ObjectId())
        
        # Create a valid JWT token for user1
        token_data = {
            "sub": "user1",
            "user_id": user1_id
        }
        valid_token = create_access_token(token_data)
        
        with patch('auth.service.get_user_by_id', new_callable=AsyncMock) as mock_get_user, \
             patch('solution.service.get_one', new_callable=AsyncMock) as mock_get_one:
            
            # Mock current user (user1)
            current_user = UserInDB(
                id=user1_id,
                username="user1",
                email="user1@example.com",
                hashed_password="fake_hash",
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            mock_get_user.return_value = current_user
            
            # Solution owned by another user (user2)
            other_solution = Solution(
                _id=ObjectId(),
                name="Other Solution",
                user_id=user2_id,  # Different user!
                versions=[]
            )
            mock_get_one.return_value = other_solution
            
            response = await async_client.patch(
                f"/solutions/{str(other_solution.id)}",
                json={"name": "Hacked Name"},
                headers={"Authorization": f"Bearer {valid_token}"}
            )
            
            # Should be forbidden
            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert "Not authorized" in response.json()["detail"]

