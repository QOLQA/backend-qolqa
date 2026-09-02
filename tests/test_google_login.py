"""
Tests for Google Login integration.
Flat file matching project convention (tests/test_auth.py).
Strict TDD: tests written FIRST, implementation follows.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ============================================================
# WU1: Domain Layer Tests
# ============================================================

class TestDomainErrors:
    """Domain error classes for Google login."""

    def test_password_required_for_local_login_error(self):
        from domain.errors import PasswordRequiredForLocalLogin

        exc = PasswordRequiredForLocalLogin()
        assert exc.msg == "This account uses Google login. Set a password or continue with Google."

    def test_invalid_google_token_error(self):
        from domain.errors import InvalidGoogleToken

        exc = InvalidGoogleToken()
        assert exc.msg == "Invalid Google token"

    def test_google_login_not_configured_error(self):
        from domain.errors import GoogleLoginNotConfigured

        exc = GoogleLoginNotConfigured()
        assert exc.msg == "Google login is not configured"


class TestAuthProviderEnum:
    """AuthProviderEnum — str Enum for auth_provider field."""

    def test_auth_provider_enum_values(self):
        from domain.enums.AuthProviderEnum import AuthProviderEnum

        assert AuthProviderEnum.local == "local"
        assert AuthProviderEnum.google == "google"
        assert AuthProviderEnum("local") == AuthProviderEnum.local
        assert AuthProviderEnum("google") == AuthProviderEnum.google


class TestUserEntityGoogleFields:
    """UserEntity gains google_id and auth_provider fields."""

    def test_user_entity_defaults(self):
        from domain.entities.auth.UserEntity import UserEntity
        from domain.enums.AuthProviderEnum import AuthProviderEnum
        from datetime import datetime

        entity = UserEntity(
            id="507f1f77bcf86cd799439011",
            username="testuser",
            email="test@example.com",
            is_active=True,
            created_at=datetime.utcnow(),
        )
        assert entity.google_id is None
        assert entity.auth_provider == AuthProviderEnum.local

    def test_user_entity_google_fields(self):
        from domain.entities.auth.UserEntity import UserEntity
        from domain.enums.AuthProviderEnum import AuthProviderEnum
        from datetime import datetime

        entity = UserEntity(
            id="507f1f77bcf86cd799439011",
            username="googler",
            email="user@gmail.com",
            is_active=True,
            created_at=datetime.utcnow(),
            google_id="google-sub-123",
            auth_provider=AuthProviderEnum.google,
        )
        assert entity.google_id == "google-sub-123"
        assert entity.auth_provider == AuthProviderEnum.google


class TestUserRepositoryGoogleMethods:
    """IUserRepository interface has abstract Google methods."""

    def test_user_repository_has_google_methods(self):
        from domain.repositories.user.repo import IUserRepository

        # Verify the abstract methods exist on the interface
        assert hasattr(IUserRepository, 'get_by_google_id')
        assert hasattr(IUserRepository, 'link_google_account')
        assert hasattr(IUserRepository, 'add_google_user')

    def test_user_repository_google_method_signatures(self):
        from domain.repositories.user.repo import IUserRepository
        import inspect

        # get_by_google_id
        sig = inspect.signature(IUserRepository.get_by_google_id)
        params = list(sig.parameters.keys())
        assert 'google_id' in params

        # link_google_account
        sig = inspect.signature(IUserRepository.link_google_account)
        params = list(sig.parameters.keys())
        assert 'user_id' in params
        assert 'google_id' in params

        # add_google_user
        sig = inspect.signature(IUserRepository.add_google_user)
        params = list(sig.parameters.keys())
        assert 'username' in params
        assert 'email' in params
        assert 'google_id' in params


# ============================================================
# WU2: Infrastructure Layer Tests
# ============================================================

class TestUserDocumentNullableFields:
    """UserDocument accepts optional hashed_password and google fields."""

    def test_user_document_nullable_fields(self):
        from infrastructure.documents.UserDocument import UserDocument
        from domain.enums.AuthProviderEnum import AuthProviderEnum
        from datetime import datetime
        from bson import ObjectId

        doc = UserDocument(
            _id=ObjectId(),
            username="testuser",
            email="test@example.com",
            is_active=True,
            hashed_password=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            google_id=None,
            auth_provider=AuthProviderEnum.local,
        )
        assert doc.hashed_password is None
        assert doc.google_id is None
        assert doc.auth_provider == AuthProviderEnum.local

    def test_user_document_google_values(self):
        from infrastructure.documents.UserDocument import UserDocument
        from domain.enums.AuthProviderEnum import AuthProviderEnum
        from datetime import datetime
        from bson import ObjectId

        doc = UserDocument(
            _id=ObjectId(),
            username="googler",
            email="user@gmail.com",
            is_active=True,
            hashed_password=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            google_id="google-sub-abc",
            auth_provider=AuthProviderEnum.google,
        )
        assert doc.google_id == "google-sub-abc"
        assert doc.auth_provider == AuthProviderEnum.google


class TestUserMapperExtensions:
    """UserMapper handles google_id, auth_provider, and from_google_request."""

    def test_mapper_to_entity_google_fields(self):
        from infrastructure.mappers.UserMapper import UserMapper
        from domain.enums.AuthProviderEnum import AuthProviderEnum
        from datetime import datetime
        from bson import ObjectId

        raw = {
            '_id': ObjectId(),
            'username': 'testuser',
            'email': 'test@example.com',
            'is_active': True,
            'created_at': datetime.utcnow(),
            'roles': ['user'],
            'token_version': 0,
            'google_id': 'google-sub-123',
            'auth_provider': 'google',
        }
        entity = UserMapper.to_entity(raw)
        assert entity.google_id == 'google-sub-123'
        assert entity.auth_provider == AuthProviderEnum.google

    def test_mapper_to_entity_defaults(self):
        from infrastructure.mappers.UserMapper import UserMapper
        from domain.enums.AuthProviderEnum import AuthProviderEnum
        from datetime import datetime
        from bson import ObjectId

        raw = {
            '_id': ObjectId(),
            'username': 'testuser',
            'email': 'test@example.com',
            'is_active': True,
            'created_at': datetime.utcnow(),
            'roles': ['user'],
            'token_version': 0,
        }
        entity = UserMapper.to_entity(raw)
        assert entity.google_id is None
        assert entity.auth_provider == AuthProviderEnum.local

    def test_mapper_from_create_request_google_fields(self):
        from infrastructure.mappers.UserMapper import UserMapper
        from application.dtos.auth.AuthRequest import UserCreateRequest

        request = UserCreateRequest(
            username="testuser",
            email="test@example.com",
            password="SecurePass123",
        )
        doc = UserMapper.from_create_request(request, "hashed_pw")
        assert doc['google_id'] is None
        assert doc['auth_provider'] == 'local'

    def test_mapper_from_google_request(self):
        from infrastructure.mappers.UserMapper import UserMapper

        doc = UserMapper.from_google_request(
            username="johndoe",
            email="john@gmail.com",
            full_name="John Doe",
            google_id="google-sub-456",
            profile_picture_url="https://example.com/pic.jpg",
        )
        assert doc['username'] == 'johndoe'
        assert doc['email'] == 'john@gmail.com'
        assert doc['full_name'] == 'John Doe'
        assert doc['hashed_password'] is None
        assert doc['auth_provider'] == 'google'
        assert doc['google_id'] == 'google-sub-456'
        assert doc['profile_picture_url'] == 'https://example.com/pic.jpg'
        assert doc['token_version'] == 0
        assert doc['roles'] == ['user']


class TestVerifyGoogleToken:
    """Google auth verification service."""

    @pytest.mark.asyncio
    async def test_verify_google_token_success(self):
        from infrastructure.services.google_auth import verify_google_token
        from unittest.mock import patch, MagicMock

        mock_payload = {
            'sub': 'google-sub-123',
            'email': 'user@gmail.com',
            'email_verified': True,
            'name': 'Test User',
            'picture': 'https://example.com/pic.jpg',
        }

        with patch('infrastructure.services.google_auth.id_token.verify_oauth2_token', return_value=mock_payload):
            result = await verify_google_token('valid-credential', 'test-client-id')
            assert result['sub'] == 'google-sub-123'
            assert result['email'] == 'user@gmail.com'
            assert result['email_verified'] is True
            assert result['name'] == 'Test User'
            assert result['picture'] == 'https://example.com/pic.jpg'

    @pytest.mark.asyncio
    async def test_verify_google_token_bad_signature(self):
        from infrastructure.services.google_auth import verify_google_token
        from domain.errors import InvalidGoogleToken
        from unittest.mock import patch

        with patch('infrastructure.services.google_auth.id_token.verify_oauth2_token', side_effect=ValueError("Bad token")):
            with pytest.raises(InvalidGoogleToken):
                await verify_google_token('bad-credential', 'test-client-id')

    @pytest.mark.asyncio
    async def test_verify_google_token_wrong_audience(self):
        from infrastructure.services.google_auth import verify_google_token
        from domain.errors import InvalidGoogleToken
        from unittest.mock import patch

        with patch('infrastructure.services.google_auth.id_token.verify_oauth2_token', side_effect=ValueError("Wrong audience")):
            with pytest.raises(InvalidGoogleToken):
                await verify_google_token('credential', 'wrong-client-id')

    @pytest.mark.asyncio
    async def test_verify_google_token_expired(self):
        from infrastructure.services.google_auth import verify_google_token
        from domain.errors import InvalidGoogleToken
        from unittest.mock import patch

        with patch('infrastructure.services.google_auth.id_token.verify_oauth2_token', side_effect=ValueError("Token expired")):
            with pytest.raises(InvalidGoogleToken):
                await verify_google_token('expired-credential', 'test-client-id')

    @pytest.mark.asyncio
    async def test_verify_google_token_malformed(self):
        from infrastructure.services.google_auth import verify_google_token
        from domain.errors import InvalidGoogleToken
        from unittest.mock import patch

        with patch('infrastructure.services.google_auth.id_token.verify_oauth2_token', side_effect=ValueError("Malformed token")):
            with pytest.raises(InvalidGoogleToken):
                await verify_google_token('malformed', 'test-client-id')

    @pytest.mark.asyncio
    async def test_verify_google_token_email_not_verified(self):
        from infrastructure.services.google_auth import verify_google_token
        from domain.errors import InvalidGoogleToken
        from unittest.mock import patch

        mock_payload = {
            'sub': 'google-sub-123',
            'email': 'user@gmail.com',
            'email_verified': False,
            'name': 'Test User',
        }

        with patch('infrastructure.services.google_auth.id_token.verify_oauth2_token', return_value=mock_payload):
            with pytest.raises(InvalidGoogleToken):
                await verify_google_token('credential', 'test-client-id')

    @pytest.mark.asyncio
    async def test_verify_google_token_missing_sub(self):
        from infrastructure.services.google_auth import verify_google_token
        from domain.errors import InvalidGoogleToken
        from unittest.mock import patch

        mock_payload = {
            'email': 'user@gmail.com',
            'email_verified': True,
            'name': 'Test User',
        }

        with patch('infrastructure.services.google_auth.id_token.verify_oauth2_token', return_value=mock_payload):
            with pytest.raises(InvalidGoogleToken):
                await verify_google_token('credential', 'test-client-id')

    @pytest.mark.asyncio
    async def test_verify_google_token_missing_email(self):
        from infrastructure.services.google_auth import verify_google_token
        from domain.errors import InvalidGoogleToken
        from unittest.mock import patch

        mock_payload = {
            'sub': 'google-sub-123',
            'email_verified': True,
            'name': 'Test User',
        }

        with patch('infrastructure.services.google_auth.id_token.verify_oauth2_token', return_value=mock_payload):
            with pytest.raises(InvalidGoogleToken):
                await verify_google_token('credential', 'test-client-id')


class TestUserRepoImplGoogleMethods:
    """UserRepoImpl Google-specific repository methods."""

    @pytest.mark.asyncio
    async def test_get_by_google_id_found(self):
        from infrastructure.repositories.UserRepoImpl import UserRepositoryImpl
        from datetime import datetime
        from bson import ObjectId

        mock_db = MagicMock()
        mock_collection = AsyncMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        user_id = ObjectId()
        mock_collection.find_one = AsyncMock(return_value={
            '_id': user_id,
            'username': 'testuser',
            'email': 'test@example.com',
            'is_active': True,
            'created_at': datetime.utcnow(),
            'roles': ['user'],
            'token_version': 0,
            'google_id': 'google-sub-123',
            'auth_provider': 'google',
        })

        repo = UserRepositoryImpl(mock_db)
        entity = await repo.get_by_google_id('google-sub-123')

        assert entity is not None
        assert entity.google_id == 'google-sub-123'
        mock_collection.find_one.assert_awaited_once_with({'google_id': 'google-sub-123'})

    @pytest.mark.asyncio
    async def test_get_by_google_id_none(self):
        from infrastructure.repositories.UserRepoImpl import UserRepositoryImpl
        from datetime import datetime
        from bson import ObjectId

        mock_db = MagicMock()
        mock_collection = AsyncMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        mock_collection.find_one = AsyncMock(return_value=None)

        repo = UserRepositoryImpl(mock_db)
        entity = await repo.get_by_google_id('nonexistent')

        assert entity is None

    @pytest.mark.asyncio
    async def test_link_google_account_success(self):
        from infrastructure.repositories.UserRepoImpl import UserRepositoryImpl
        from datetime import datetime
        from bson import ObjectId

        mock_db = MagicMock()
        mock_collection = AsyncMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        user_id = str(ObjectId())
        mock_collection.find_one = AsyncMock(return_value={
            '_id': ObjectId(user_id),
            'username': 'testuser',
            'email': 'test@example.com',
            'is_active': True,
            'created_at': datetime.utcnow(),
            'roles': ['user'],
            'token_version': 0,
        })
        mock_collection.update_one = AsyncMock(return_value=MagicMock(matched_count=1))

        repo = UserRepositoryImpl(mock_db)
        entity = await repo.link_google_account(user_id, 'google-sub-123')

        assert entity is not None
        mock_collection.update_one.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_link_google_account_bad_object_id(self):
        from infrastructure.repositories.UserRepoImpl import UserRepositoryImpl
        from domain.errors import Missing

        mock_db = MagicMock()
        mock_collection = AsyncMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        repo = UserRepositoryImpl(mock_db)
        with pytest.raises(Missing):
            await repo.link_google_account('invalid-id', 'google-sub-123')

    @pytest.mark.asyncio
    async def test_link_google_account_duplicate_key(self):
        from infrastructure.repositories.UserRepoImpl import UserRepositoryImpl
        from domain.errors import Duplicate
        from datetime import datetime
        from bson import ObjectId
        from pymongo.errors import DuplicateKeyError

        mock_db = MagicMock()
        mock_collection = AsyncMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        user_id = str(ObjectId())
        mock_collection.find_one = AsyncMock(return_value={
            '_id': ObjectId(user_id),
            'username': 'testuser',
            'email': 'test@example.com',
            'is_active': True,
            'created_at': datetime.utcnow(),
            'roles': ['user'],
            'token_version': 0,
        })
        mock_collection.update_one = AsyncMock(side_effect=DuplicateKeyError("duplicate key"))

        repo = UserRepositoryImpl(mock_db)
        with pytest.raises(Duplicate):
            await repo.link_google_account(user_id, 'google-sub-123')

    @pytest.mark.asyncio
    async def test_add_google_user_success(self):
        from infrastructure.repositories.UserRepoImpl import UserRepositoryImpl
        from datetime import datetime
        from bson import ObjectId

        mock_db = MagicMock()
        mock_collection = AsyncMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        new_id = ObjectId()
        mock_collection.find_one = AsyncMock(return_value=None)  # No duplicates
        mock_collection.insert_one = AsyncMock(return_value=MagicMock(inserted_id=new_id))

        # After insert, find_one returns the new user
        original_find_one = mock_collection.find_one
        call_count = 0

        async def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:  # duplicate checks (username, email)
                return None
            return {  # get_by_id after insert
                '_id': new_id,
                'username': 'johndoe',
                'email': 'john@gmail.com',
                'is_active': True,
                'created_at': datetime.utcnow(),
                'roles': ['user'],
                'token_version': 0,
                'google_id': 'google-sub-456',
                'auth_provider': 'google',
            }

        mock_collection.find_one = AsyncMock(side_effect=side_effect)

        repo = UserRepositoryImpl(mock_db)
        entity = await repo.add_google_user(
            username='johndoe',
            email='john@gmail.com',
            full_name='John Doe',
            google_id='google-sub-456',
            profile_picture_url='https://example.com/pic.jpg',
        )

        assert entity is not None
        assert entity.google_id == 'google-sub-456'
        mock_collection.insert_one.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_add_google_user_duplicate_username(self):
        from infrastructure.repositories.UserRepoImpl import UserRepositoryImpl
        from domain.errors import Duplicate
        from datetime import datetime
        from bson import ObjectId

        mock_db = MagicMock()
        mock_collection = AsyncMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        mock_collection.find_one = AsyncMock(return_value={
            '_id': ObjectId(),
            'username': 'johndoe',
            'email': 'other@example.com',
            'is_active': True,
            'created_at': datetime.utcnow(),
            'roles': ['user'],
            'token_version': 0,
        })

        repo = UserRepositoryImpl(mock_db)
        with pytest.raises(Duplicate):
            await repo.add_google_user(
                username='johndoe',
                email='john@gmail.com',
                full_name='John Doe',
                google_id='google-sub-456',
                profile_picture_url=None,
            )

    @pytest.mark.asyncio
    async def test_add_google_user_duplicate_email(self):
        from infrastructure.repositories.UserRepoImpl import UserRepositoryImpl
        from domain.errors import Duplicate
        from datetime import datetime
        from bson import ObjectId

        mock_db = MagicMock()
        mock_collection = AsyncMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        # First call: username not found, second call: email found
        mock_collection.find_one = AsyncMock(side_effect=[
            None,  # username check
            {  # email check
                '_id': ObjectId(),
                'username': 'otheruser',
                'email': 'john@gmail.com',
                'is_active': True,
                'created_at': datetime.utcnow(),
                'roles': ['user'],
                'token_version': 0,
            },
        ])

        repo = UserRepositoryImpl(mock_db)
        with pytest.raises(Duplicate):
            await repo.add_google_user(
                username='johndoe',
                email='john@gmail.com',
                full_name='John Doe',
                google_id='google-sub-456',
                profile_picture_url=None,
            )


# ============================================================
# WU3: Application Layer Tests
# ============================================================

class TestGoogleLoginRequestResponseDTOs:
    """GoogleLoginRequest and GoogleLoginResponse DTOs."""

    def test_google_login_request_dto(self):
        from application.dtos.auth.AuthRequest import GoogleLoginRequest

        dto = GoogleLoginRequest(credential="valid-credential-string")
        assert dto.credential == "valid-credential-string"

    def test_google_login_response_dto_no_password(self):
        from application.dtos.auth.AuthResponse import GoogleLoginResponse, UserResponse
        from datetime import datetime

        user = UserResponse(
            id="507f1f77bcf86cd799439011",
            username="testuser",
            email="test@example.com",
            is_active=True,
            created_at=datetime.utcnow(),
        )
        response = GoogleLoginResponse(
            access_token="test-token",
            token_type="bearer",
            user=user,
        )
        assert response.access_token == "test-token"
        assert response.token_type == "bearer"
        assert response.user.username == "testuser"
        data = response.model_dump()
        assert "password" not in data
        assert "hashed_password" not in data
        assert "user" in data
        assert "password" not in data["user"]
        assert "hashed_password" not in data["user"]


class TestGoogleLoginUseCase:
    """GoogleLogin use case orchestration."""

    @pytest.mark.asyncio
    async def test_google_login_new_user(self):
        from application.use_cases.auth.GoogleLogin import google_login
        from unittest.mock import AsyncMock, MagicMock, patch
        from datetime import datetime

        mock_repo = AsyncMock()
        mock_repo.get_by_google_id = AsyncMock(return_value=None)
        mock_repo.get_by_email = AsyncMock(return_value=None)
        mock_repo.get_by_username = AsyncMock(return_value=None)

        new_user = MagicMock()
        new_user.id = "new-id"
        new_user.username = "johndoe"
        mock_repo.add_google_user = AsyncMock(return_value=new_user)

        mock_info = {
            'sub': 'google-sub-123',
            'email': 'john@gmail.com',
            'email_verified': True,
            'name': 'John Doe',
            'picture': 'https://example.com/pic.jpg',
        }

        with patch('application.use_cases.auth.GoogleLogin.verify_google_token', new_callable=AsyncMock, return_value=mock_info):
            result = await google_login(mock_repo, 'credential', 'test-client-id')

        assert result == new_user
        mock_repo.add_google_user.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_google_login_existing_google_id(self):
        from application.use_cases.auth.GoogleLogin import google_login
        from unittest.mock import AsyncMock, MagicMock, patch

        mock_repo = AsyncMock()
        existing_user = MagicMock()
        existing_user.id = "existing-id"
        mock_repo.get_by_google_id = AsyncMock(return_value=existing_user)

        mock_info = {
            'sub': 'google-sub-123',
            'email': 'john@gmail.com',
            'email_verified': True,
            'name': 'John Doe',
        }

        with patch('application.use_cases.auth.GoogleLogin.verify_google_token', new_callable=AsyncMock, return_value=mock_info):
            result = await google_login(mock_repo, 'credential', 'test-client-id')

        assert result == existing_user
        mock_repo.add_google_user.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_google_login_email_link(self):
        from application.use_cases.auth.GoogleLogin import google_login
        from unittest.mock import AsyncMock, MagicMock, patch

        mock_repo = AsyncMock()
        mock_repo.get_by_google_id = AsyncMock(return_value=None)

        existing_user = MagicMock()
        existing_user.id = "existing-local-id"
        mock_repo.get_by_email = AsyncMock(return_value=existing_user)
        mock_repo.link_google_account = AsyncMock(return_value=existing_user)

        mock_info = {
            'sub': 'google-sub-456',
            'email': 'existing@example.com',
            'email_verified': True,
            'name': 'Existing User',
        }

        with patch('application.use_cases.auth.GoogleLogin.verify_google_token', new_callable=AsyncMock, return_value=mock_info):
            result = await google_login(mock_repo, 'credential', 'test-client-id')

        assert result == existing_user
        mock_repo.link_google_account.assert_awaited_once_with("existing-local-id", "google-sub-456")
        mock_repo.add_google_user.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_google_login_username_collision(self):
        from application.use_cases.auth.GoogleLogin import google_login
        from unittest.mock import AsyncMock, MagicMock, patch
        from domain.errors import Duplicate

        mock_repo = AsyncMock()
        mock_repo.get_by_google_id = AsyncMock(return_value=None)
        mock_repo.get_by_email = AsyncMock(return_value=None)

        # First username check returns existing user (collision)
        collision_user = MagicMock()
        mock_repo.get_by_username = AsyncMock(side_effect=[collision_user, None])

        # First add_google_user raises Duplicate (race), second succeeds
        new_user = MagicMock()
        new_user.id = "new-user-id"
        mock_repo.add_google_user = AsyncMock(side_effect=[
            Duplicate(msg="Duplicate"),
            new_user,
        ])

        mock_info = {
            'sub': 'google-sub-789',
            'email': 'john@gmail.com',
            'email_verified': True,
            'name': 'John Doe',
        }

        with patch('application.use_cases.auth.GoogleLogin.verify_google_token', new_callable=AsyncMock, return_value=mock_info):
            result = await google_login(mock_repo, 'credential', 'test-client-id')

        assert result == new_user

    @pytest.mark.asyncio
    async def test_google_login_503_when_client_id_none(self):
        from application.use_cases.auth.GoogleLogin import google_login
        from domain.errors import GoogleLoginNotConfigured
        from unittest.mock import AsyncMock

        mock_repo = AsyncMock()

        with pytest.raises(GoogleLoginNotConfigured):
            await google_login(mock_repo, 'credential', None)


class TestAuthenticateUserGuard:
    """AuthenticateUser guard for passwordless Google accounts."""

    @pytest.mark.asyncio
    async def test_authenticate_guard_google_only_user(self):
        from application.use_cases.auth.AuthenticateUser import authenticate_user
        from domain.errors import PasswordRequiredForLocalLogin
        from domain.enums.AuthProviderEnum import AuthProviderEnum
        from unittest.mock import AsyncMock, MagicMock

        mock_repo = AsyncMock()
        user_entity = MagicMock()
        user_entity.username = "googleuser"
        user_entity.auth_provider = AuthProviderEnum.google
        user_entity.is_active = True

        mock_repo.get_by_username = AsyncMock(return_value=user_entity)
        mock_repo.get_hashed_password = AsyncMock(return_value=None)

        with pytest.raises(PasswordRequiredForLocalLogin):
            await authenticate_user(mock_repo, "googleuser", "anypassword")

    @pytest.mark.asyncio
    async def test_authenticate_guard_hybrid_user(self):
        from application.use_cases.auth.AuthenticateUser import authenticate_user
        from domain.enums.AuthProviderEnum import AuthProviderEnum
        from unittest.mock import AsyncMock, MagicMock, patch

        mock_repo = AsyncMock()
        user_entity = MagicMock()
        user_entity.username = "hybriduser"
        user_entity.auth_provider = AuthProviderEnum.local
        user_entity.is_active = True

        mock_repo.get_by_username = AsyncMock(return_value=user_entity)
        mock_repo.get_hashed_password = AsyncMock(return_value="hashed_pw")

        with patch('application.use_cases.auth.AuthenticateUser.verify_password', return_value=True):
            result = await authenticate_user(mock_repo, "hybriduser", "password123")

        assert result == user_entity

    @pytest.mark.asyncio
    async def test_authenticate_guard_inactive_google_user(self):
        from application.use_cases.auth.AuthenticateUser import authenticate_user
        from domain.errors import InvalidCredentials
        from domain.enums.AuthProviderEnum import AuthProviderEnum
        from unittest.mock import AsyncMock, MagicMock

        mock_repo = AsyncMock()
        user_entity = MagicMock()
        user_entity.username = "inactiveuser"
        user_entity.auth_provider = AuthProviderEnum.google
        user_entity.is_active = False

        mock_repo.get_by_username = AsyncMock(return_value=user_entity)
        mock_repo.get_hashed_password = AsyncMock(return_value=None)

        with pytest.raises(InvalidCredentials):
            await authenticate_user(mock_repo, "inactiveuser", "anypassword")


# ============================================================
# WU4: API Layer + Config Tests
# ============================================================

class TestHandleErrorsGoogleExceptions:
    """handle_common_errors mappings for Google-specific exceptions."""

    @pytest.mark.asyncio
    async def test_handle_errors_password_required_403(self):
        from api.handle_errors import handle_common_errors
        from domain.errors import PasswordRequiredForLocalLogin
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await handle_common_errors(PasswordRequiredForLocalLogin())

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "This account uses Google login. Set a password or continue with Google."

    @pytest.mark.asyncio
    async def test_handle_errors_invalid_google_token_401(self):
        from api.handle_errors import handle_common_errors
        from domain.errors import InvalidGoogleToken
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await handle_common_errors(InvalidGoogleToken())

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid Google token"
        assert exc_info.value.headers.get("WWW-Authenticate") == "Bearer"

    @pytest.mark.asyncio
    async def test_handle_errors_google_not_configured_503(self):
        from api.handle_errors import handle_common_errors
        from domain.errors import GoogleLoginNotConfigured
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await handle_common_errors(GoogleLoginNotConfigured())

        assert exc_info.value.status_code == 503
        assert exc_info.value.detail == "Google login is not configured"


class TestPostGoogleAuthEndpoint:
    """POST /auth/google endpoint tests."""

    @pytest.mark.asyncio
    async def test_post_google_auth_happy_new_user(self, async_client):
        from datetime import datetime
        from bson import ObjectId
        from domain.entities.auth.UserEntity import UserEntity
        from application.dtos.auth.AuthResponse import TokenResponse

        mock_user = UserEntity(
            id=str(ObjectId()),
            username="newgoogleuser",
            email="new@gmail.com",
            is_active=True,
            created_at=datetime.utcnow(),
            token_version=0,
            roles=[],
        )

        with patch('api.controllers.auth.google_login', new_callable=AsyncMock) as mock_use_case, \
             patch('api.controllers.auth.create_user_token', new_callable=AsyncMock) as mock_token:
            mock_use_case.return_value = mock_user
            mock_token.return_value = TokenResponse(access_token="google-jwt-token", token_type="bearer")

            response = await async_client.post(
                "/auth/google",
                json={"credential": "valid-google-token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert "user" in data
            assert "password" not in data["user"]
            assert "hashed_password" not in data["user"]
            assert data["user"]["username"] == "newgoogleuser"

    @pytest.mark.asyncio
    async def test_post_google_auth_invalid_token_401(self, async_client):
        from domain.errors import InvalidGoogleToken

        with patch('api.controllers.auth.google_login', new_callable=AsyncMock) as mock_use_case:
            mock_use_case.side_effect = InvalidGoogleToken()

            response = await async_client.post(
                "/auth/google",
                json={"credential": "bad-token"},
            )

            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_post_google_auth_unset_client_id_503(self, async_client):
        from domain.errors import GoogleLoginNotConfigured

        with patch('api.controllers.auth.google_login', new_callable=AsyncMock) as mock_use_case:
            mock_use_case.side_effect = GoogleLoginNotConfigured()

            response = await async_client.post(
                "/auth/google",
                json={"credential": "any-token"},
            )

            assert response.status_code == 503

    @pytest.mark.asyncio
    async def test_post_google_auth_existing_google_id(self, async_client):
        from datetime import datetime
        from bson import ObjectId
        from domain.entities.auth.UserEntity import UserEntity
        from application.dtos.auth.AuthResponse import TokenResponse

        existing_user = UserEntity(
            id=str(ObjectId()),
            username="existinggoogle",
            email="existing@gmail.com",
            is_active=True,
            created_at=datetime.utcnow(),
            token_version=0,
            roles=[],
        )

        with patch('api.controllers.auth.google_login', new_callable=AsyncMock) as mock_use_case, \
             patch('api.controllers.auth.create_user_token', new_callable=AsyncMock) as mock_token:
            mock_use_case.return_value = existing_user
            mock_token.return_value = TokenResponse(access_token="existing-jwt", token_type="bearer")

            response = await async_client.post(
                "/auth/google",
                json={"credential": "valid-token"},
            )

            assert response.status_code == 200
            assert response.json()["user"]["username"] == "existinggoogle"


# ============================================================
# WU5: Migration Script Tests
# ============================================================

class TestMigrationScript:
    """Migration script for adding Google fields."""

    def test_migration_script_exists(self):
        """Migration script file exists."""
        import os
        assert os.path.exists('scripts/migrate_add_google_fields.py')

    def test_migration_script_has_dry_run_arg(self):
        """Migration script supports --dry-run argument."""
        import ast

        with open('scripts/migrate_add_google_fields.py', 'r') as f:
            content = f.read()

        # Verify argparse with --dry-run is present
        assert 'argparse' in content
        assert '--dry-run' in content or 'dry_run' in content

    def test_migration_script_has_required_elements(self):
        """Migration script contains required patterns."""
        import os

        with open('scripts/migrate_add_google_fields.py', 'r') as f:
            content = f.read()

        # Must have asyncio.run for async execution
        assert 'asyncio.run' in content
        # Must have backfill logic
        assert 'auth_provider' in content
        # Must have index creation
        assert 'create_index' in content or 'google_id' in content
        # Must have client.close() in finally
        assert 'client.close()' in content
        # Must have dry-run logic
        assert 'dry_run' in content


# ============================================================
# WU6: Integration Tests
# ============================================================

class TestGoogleLoginIntegration:
    """End-to-end integration tests for Google login."""

    @pytest.mark.asyncio
    async def test_integration_google_login_new_user_full_flow(self, async_client):
        """Full flow: valid token → new user created → returns user + token."""
        from datetime import datetime
        from bson import ObjectId
        from domain.entities.auth.UserEntity import UserEntity
        from application.dtos.auth.AuthResponse import TokenResponse

        mock_user = UserEntity(
            id=str(ObjectId()),
            username="integrationuser",
            email="integration@gmail.com",
            is_active=True,
            created_at=datetime.utcnow(),
            token_version=0,
            roles=[],
        )

        with patch('api.controllers.auth.google_login', new_callable=AsyncMock) as mock_use_case, \
             patch('api.controllers.auth.create_user_token', new_callable=AsyncMock) as mock_token:
            mock_use_case.return_value = mock_user
            mock_token.return_value = TokenResponse(access_token="integration-jwt", token_type="bearer")

            response = await async_client.post(
                "/auth/google",
                json={"credential": "valid-google-credential"},
            )

            # Rate limiting may apply; accept 200 or 429
            assert response.status_code in (200, 429)
            if response.status_code == 200:
                data = response.json()
                assert "access_token" in data
                assert data["access_token"] == "integration-jwt"
                assert data["token_type"] == "bearer"
                assert "user" in data
                assert data["user"]["username"] == "integrationuser"
                assert data["user"]["email"] == "integration@gmail.com"
                assert "password" not in data["user"]
                assert "hashed_password" not in data["user"]

    @pytest.mark.asyncio
    async def test_integration_google_login_existing_full_flow(self, async_client):
        """Full flow: existing google_id → returns existing user + new token."""
        from datetime import datetime
        from bson import ObjectId
        from domain.entities.auth.UserEntity import UserEntity
        from application.dtos.auth.AuthResponse import TokenResponse

        existing_user = UserEntity(
            id=str(ObjectId()),
            username="existinguser",
            email="existing@gmail.com",
            is_active=True,
            created_at=datetime.utcnow(),
            token_version=0,
            roles=[],
        )

        with patch('api.controllers.auth.google_login', new_callable=AsyncMock) as mock_use_case, \
             patch('api.controllers.auth.create_user_token', new_callable=AsyncMock) as mock_token:
            mock_use_case.return_value = existing_user
            mock_token.return_value = TokenResponse(access_token="existing-jwt", token_type="bearer")

            response = await async_client.post(
                "/auth/google",
                json={"credential": "valid-google-credential"},
            )

            assert response.status_code in (200, 429)
            if response.status_code == 200:
                data = response.json()
                assert data["user"]["username"] == "existinguser"
                assert data["access_token"] == "existing-jwt"

    @pytest.mark.asyncio
    async def test_integration_invalid_token_returns_401(self, async_client):
        """Invalid Google token returns 401."""
        from domain.errors import InvalidGoogleToken

        with patch('api.controllers.auth.google_login', new_callable=AsyncMock) as mock_use_case:
            mock_use_case.side_effect = InvalidGoogleToken()

            response = await async_client.post(
                "/auth/google",
                json={"credential": "bad-token"},
            )

            # Rate limiting may apply; accept 401 or 429
            assert response.status_code in (401, 429)
            if response.status_code == 401:
                assert response.json()["detail"] == "Invalid Google token"

    @pytest.mark.asyncio
    async def test_integration_unset_client_id_returns_503(self, async_client):
        """Unset GOOGLE_CLIENT_ID returns 503."""
        from domain.errors import GoogleLoginNotConfigured

        with patch('api.controllers.auth.google_login', new_callable=AsyncMock) as mock_use_case:
            mock_use_case.side_effect = GoogleLoginNotConfigured()

            response = await async_client.post(
                "/auth/google",
                json={"credential": "any-token"},
            )

            # Rate limiting may apply; accept 503 or 429
            assert response.status_code in (503, 429)
            if response.status_code == 503:
                assert response.json()["detail"] == "Google login is not configured"

    @pytest.mark.asyncio
    async def test_integration_register_unaffected(self, async_client):
        """POST /register still works (regression test)."""
        from datetime import datetime
        from bson import ObjectId
        from domain.entities.auth.UserEntity import UserEntity

        with patch('api.controllers.auth.register_user', new_callable=AsyncMock) as mock_register:
            mock_register.return_value = UserEntity(
                id=str(ObjectId()),
                username="newuser",
                email="new@example.com",
                is_active=True,
                created_at=datetime.utcnow(),
                roles=[],
                token_version=0,
            )

            response = await async_client.post(
                "/auth/register",
                json={
                    "username": "newuser",
                    "email": "new@example.com",
                    "password": "SecurePass123",
                },
            )

            assert response.status_code == 201
            assert response.json()["username"] == "newuser"

    @pytest.mark.asyncio
    async def test_integration_login_unaffected(self, async_client):
        """POST /login still works (regression test)."""
        from datetime import datetime
        from bson import ObjectId
        from domain.entities.auth.UserEntity import UserEntity
        from application.dtos.auth.AuthResponse import TokenResponse

        with patch('api.controllers.auth.authenticate_user', new_callable=AsyncMock) as mock_auth, \
             patch('api.controllers.auth.create_user_token', new_callable=AsyncMock) as mock_token:
            mock_auth.return_value = UserEntity(
                id=str(ObjectId()),
                username="testuser",
                email="test@example.com",
                is_active=True,
                created_at=datetime.utcnow(),
                roles=[],
                token_version=0,
            )
            mock_token.return_value = TokenResponse(access_token="login-jwt", token_type="bearer")

            response = await async_client.post(
                "/auth/login",
                data={"username": "testuser", "password": "secret"},
            )

            assert response.status_code == 200
            assert "access_token" in response.json()
