from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional

from domain.entities.auth.UserEntity import UserEntity
from domain.errors import InvalidCredentials, PasswordRequiredForLocalLogin
from domain.enums.AuthProviderEnum import AuthProviderEnum


Entity = TypeVar('Entity', bound=UserEntity)


class IUserRepository(ABC, Generic[Entity]):
    """User repository port (interface)."""

    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[Entity]:
        """Retrieve a user by ID."""
        ...

    @abstractmethod
    async def get_all(self) -> List[Entity]:
        """Retrieve all users."""
        ...

    @abstractmethod
    async def save(self, entity: Entity) -> Entity:
        """Save (create or update) a user entity."""
        ...

    @abstractmethod
    async def delete(self, id: str) -> None:
        """Delete a user by ID."""
        ...

    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[Entity]:
        """Retrieve a user by username."""
        ...

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[Entity]:
        """Retrieve a user by email."""
        ...

    @abstractmethod
    async def get_by_google_id(self, google_id: str) -> Optional[Entity]:
        """Retrieve a user by Google ID."""
        ...

    @abstractmethod
    async def link_google_account(self, user_id: str, google_id: str) -> Entity:
        """Link a Google account to an existing user."""
        ...

    @abstractmethod
    async def add_google_user(
        self,
        username: str,
        email: str,
        full_name: Optional[str],
        google_id: str,
        profile_picture_url: Optional[str],
    ) -> Entity:
        """Create a new Google-authenticated user (no password)."""
        ...

    @abstractmethod
    async def verify_credentials(self, username: str, password: str) -> Entity:
        """Verify user credentials by username or email and password.

        Args:
            username: Username or email to authenticate
            password: Plain text password

        Returns:
            UserEntity if authentication successful

        Raises:
            InvalidCredentials: If username/password combination is invalid or user is inactive
            PasswordRequiredForLocalLogin: If user has no local password (Google-only account)
        """
        ...