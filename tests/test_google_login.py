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
