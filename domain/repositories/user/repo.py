from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from domain.entities.auth.UserEntity import UserEntity

Entity = TypeVar('Entity', bound=UserEntity)


class IUserRepository(ABC, Generic[Entity]):
    """User repository port (interface)."""

    @abstractmethod
    async def get_by_id(self, id: str) -> Entity | None:
        """Retrieve a user by ID."""
        ...

    @abstractmethod
    async def get_all(self) -> list[Entity]:
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
    async def get_by_username(self, username: str) -> Entity | None:
        """Retrieve a user by username."""
        ...

    @abstractmethod
    async def get_by_email(self, email: str) -> Entity | None:
        """Retrieve a user by email."""
        ...

    @abstractmethod
    async def get_by_google_id(self, google_id: str) -> Entity | None:
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
        full_name: str | None,
        google_id: str,
        profile_picture_url: str | None,
    ) -> Entity:
        """Create a new Google-authenticated user (no password)."""
        ...

    @abstractmethod
    async def add_local_user(
        self,
        username: str,
        email: str,
        full_name: str | None,
        password: str,
    ) -> Entity:
        """Create a new local (email/password) user.

        The repository hashes the password before persistence — the plain
        password never reaches the database and never crosses back to the
        caller.
        """
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