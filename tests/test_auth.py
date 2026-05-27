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
        # Mock use case functions (clean architecture paths)
        with patch('api.controllers.auth.authenticate_user', new_callable=AsyncMock) as mock_auth, \
             patch('api.controllers.auth.create_user_token', new_callable=AsyncMock) as mock_token:
            
            from domain.entities.auth.UserEntity import UserEntity
            from application.dtos.auth.AuthResponse import TokenResponse
            from datetime import datetime
            
            mock_entity = UserEntity(
                id="507f1f77bcf86cd799439011",
                username="testuser",
                email="test@example.com",
                is_active=True,
                created_at=datetime.utcnow(),
                roles=[],
                token_version=0,
            )
            mock_auth.return_value = mock_entity
            mock_token.return_value = TokenResponse(
                access_token="fake_token",
                token_type="bearer",
            )
            
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
        from domain.errors import InvalidCredentials

        with patch('api.controllers.auth.authenticate_user', new_callable=AsyncMock) as mock_auth:
            mock_auth.side_effect = InvalidCredentials()

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
        from datetime import datetime
        from bson import ObjectId
        from main import app as fastapi_app
        from api.dependencies.auth import get_current_user
        from domain.entities.auth.UserEntity import UserEntity

        user_id = str(ObjectId())

        mock_entity = UserEntity(
            id=user_id,
            username="testuser",
            email="test@example.com",
            is_active=True,
            created_at=datetime.utcnow(),
            token_version=0,
            roles=[],
        )

        async def override_current_user():
            return mock_entity

        fastapi_app.dependency_overrides[get_current_user] = override_current_user

        try:
            with patch('api.controllers.solution.get_all_solutions_for_user', new_callable=AsyncMock) as mock_get_all:
                mock_get_all.return_value = []

                response = await async_client.get(
                    "/solutions",
                    headers={"Authorization": "Bearer fake_but_bypassed"}
                )

                assert response.status_code == status.HTTP_200_OK
                assert response.json() == []
        finally:
            fastapi_app.dependency_overrides.pop(get_current_user, None)
    
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
                "roles": [],
                "token_version": 0,
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
        with patch('api.controllers.auth.register_user', new_callable=AsyncMock) as mock_register:
            from domain.entities.auth.UserEntity import UserEntity
            from datetime import datetime
            
            mock_register.return_value = UserEntity(
                id="507f1f77bcf86cd799439011",
                username="newuser",
                email="newuser@example.com",
                is_active=True,
                created_at=datetime.utcnow(),
                roles=[],
                token_version=0,
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
        with patch('api.controllers.auth.register_user', new_callable=AsyncMock) as mock_register:
            from domain.errors import Duplicate
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
        from infrastructure.jwt import create_access_token
        
        token = create_access_token(data={"sub": "user123"})
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_decode_token_valid(self):
        """Test decoding valid JWT token"""
        from infrastructure.jwt import create_access_token, decode_access_token
        
        token = create_access_token(data={"sub": "user123", "user_id": "456"})
        payload = decode_access_token(token)
        
        assert payload["sub"] == "user123"
        assert payload["user_id"] == "456"
        assert "exp" in payload
    
    def test_decode_token_invalid(self):
        """Test decoding invalid JWT token raises domain error (not HTTPException)"""
        from infrastructure.jwt import decode_access_token
        from domain.errors import InvalidToken

        with pytest.raises(InvalidToken):
            decode_access_token("invalid.token.here")
    
    def test_token_includes_expiration(self):
        """Test that generated tokens include expiration time"""
        from infrastructure.jwt import create_access_token, decode_access_token
        
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
        from infrastructure.password import get_password_hash
        
        hashed = get_password_hash("mypassword")
        
        assert hashed != "mypassword"
        assert len(hashed) > 0
        assert hashed.startswith("$2b$")  # bcrypt hash starts with $2b$
    
    def test_verify_password_correct(self):
        """Test password verification with correct password"""
        from infrastructure.password import get_password_hash, verify_password
        
        password = "mypassword"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password"""
        from infrastructure.password import get_password_hash, verify_password
        
        hashed = get_password_hash("mypassword")
        
        assert verify_password("wrongpassword", hashed) is False


@pytest.mark.auth
class TestAuthorizationRoles:
    """Test suite for role-based authorization"""

    @pytest.mark.asyncio
    async def test_admin_can_access_admin_endpoint(self, async_client):
        """Test admin user can access admin endpoints — receives 200, not 403"""
        from datetime import datetime
        from bson import ObjectId
        from main import app as fastapi_app
        from api.dependencies.auth import get_current_user, require_admin
        from domain.entities.auth.UserEntity import UserEntity
        from domain.enums.RoleEnum import RoleEnum

        admin_user = UserEntity(
            id=str(ObjectId()),
            username="adminuser",
            email="admin@example.com",
            is_active=True,
            created_at=datetime.utcnow(),
            token_version=0,
            roles=[RoleEnum.admin],
        )

        async def override_current_user() -> UserEntity:
            return admin_user

        async def override_require_admin() -> UserEntity:
            return admin_user

        fastapi_app.dependency_overrides[get_current_user] = override_current_user
        fastapi_app.dependency_overrides[require_admin] = override_require_admin

        try:
            with patch('api.controllers.admin.UserRepositoryImpl.get_all', new_callable=AsyncMock) as mock_get_all:
                mock_get_all.return_value = []
                response = await async_client.get("/admin/users")
        finally:
            fastapi_app.dependency_overrides.pop(get_current_user, None)
            fastapi_app.dependency_overrides.pop(require_admin, None)

        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_regular_user_denied_admin_endpoint(self, async_client):
        """Test regular user (no admin role) receives 403 on admin endpoints"""
        from datetime import datetime
        from bson import ObjectId
        from main import app as fastapi_app
        from api.dependencies.auth import get_current_user
        from domain.entities.auth.UserEntity import UserEntity
        from infrastructure.jwt import create_access_token

        regular_user = UserEntity(
            id=str(ObjectId()),
            username="regularuser",
            email="regular@example.com",
            is_active=True,
            created_at=datetime.utcnow(),
            token_version=0,
            roles=[],
        )

        async def override_current_user() -> UserEntity:
            return regular_user

        token = create_access_token({
            "sub": regular_user.username,
            "user_id": regular_user.id,
            "roles": [],
            "token_version": 0,
        })

        fastapi_app.dependency_overrides[get_current_user] = override_current_user

        try:
            response = await async_client.get(
                "/admin/users",
                headers={"Authorization": f"Bearer {token}"},
            )
        finally:
            fastapi_app.dependency_overrides.pop(get_current_user, None)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_user_can_only_modify_own_solutions(self, async_client):
        """Test users can only modify their own solutions"""
        from datetime import datetime
        from bson import ObjectId
        from main import app as fastapi_app
        from api.dependencies.auth import get_current_user
        from domain.entities.auth.UserEntity import UserEntity

        user1_id = str(ObjectId())

        current_user = UserEntity(
            id=user1_id,
            username="user1",
            email="user1@example.com",
            is_active=True,
            created_at=datetime.utcnow(),
            token_version=0,
            roles=[],
        )

        async def override_current_user() -> UserEntity:
            return current_user

        fastapi_app.dependency_overrides[get_current_user] = override_current_user

        try:
            with patch('api.controllers.solution.update_solution', new_callable=AsyncMock) as mock_get_one:
                from domain.errors import Forbidden
                mock_get_one.side_effect = Forbidden(msg="Not authorized to modify this solution")
                other_solution_id = str(ObjectId())

                response = await async_client.patch(
                    f"/solutions/{other_solution_id}",
                    json={"name": "Hacked Name"},
                    headers={"Authorization": "Bearer fake_but_bypassed"}
                )

                assert response.status_code == status.HTTP_403_FORBIDDEN
                assert "Not authorized" in response.json()["detail"]
        finally:
            fastapi_app.dependency_overrides.pop(get_current_user, None)

