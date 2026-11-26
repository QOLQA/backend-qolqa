from dataclasses import dataclass, field
from datetime import UTC, datetime

from domain.enums.AuthProviderEnum import AuthProviderEnum
from domain.enums.RoleEnum import RoleEnum
from domain.errors import Forbidden


@dataclass
class UserEntity:
    """Pure domain entity for a User. Zero infrastructure dependencies."""

    id: str
    username: str
    email: str
    full_name: str | None = None
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    profile_picture_url: str | None = None
    roles: list[RoleEnum] = field(default_factory=lambda: [RoleEnum.user])
    token_version: int = 0
    google_id: str | None = None
    auth_provider: AuthProviderEnum = AuthProviderEnum.local

    # ------------------------------------------------------------------ #
    # Factory Methods
    # ------------------------------------------------------------------ #

    @classmethod
    def create_local(
        cls,
        id: str,
        username: str,
        email: str,
        full_name: str | None = None,
    ) -> "UserEntity":
        """Create a new local (email/password) user."""
        if not username or not username.strip():
            raise ValueError("Username cannot be empty")
        if not email or not email.strip():
            raise ValueError("Email cannot be empty")

        return cls(
            id=id,
            username=username.strip().lower(),
            email=email.strip().lower(),
            full_name=full_name.strip() if full_name else None,
            is_active=True,
            created_at=datetime.now(UTC),
            roles=[RoleEnum.user],
            token_version=0,
            auth_provider=AuthProviderEnum.local,
        )

    @classmethod
    def create_google(
        cls,
        id: str,
        username: str,
        email: str,
        full_name: str | None = None,
        google_id: str = "",
        profile_picture_url: str | None = None,
    ) -> "UserEntity":
        """Create a new Google-authenticated user."""
        if not username or not username.strip():
            raise ValueError("Username cannot be empty")
        if not email or not email.strip():
            raise ValueError("Email cannot be empty")
        if not google_id:
            raise ValueError("Google ID is required for Google users")

        return cls(
            id=id,
            username=username.strip(),
            email=email.strip().lower(),
            full_name=full_name.strip() if full_name else None,
            is_active=True,
            created_at=datetime.now(UTC),
            roles=[RoleEnum.user],
            token_version=0,
            google_id=google_id,
            profile_picture_url=profile_picture_url,
            auth_provider=AuthProviderEnum.google,
        )

    # ------------------------------------------------------------------ #
    # Business Mutation Methods
    # ------------------------------------------------------------------ #

    def update_profile(
        self,
        username: str | None = None,
        email: str | None = None,
        full_name: str | None = None,
    ) -> None:
        """Update user profile fields."""
        if username is not None:
            if not username.strip():
                raise ValueError("Username cannot be empty")
            self.username = username.strip().lower()

        if email is not None:
            if not email.strip():
                raise ValueError("Email cannot be empty")
            self.email = email.strip().lower()

        if full_name is not None:
            self.full_name = full_name.strip() if full_name else None

    def change_password(self) -> None:
        """Mark password as changed — increments token_version to invalidate existing tokens."""
        self.token_version += 1

    def link_google(self, google_id: str, profile_picture_url: str | None = None) -> None:
        """Link a Google account to this user."""
        if not google_id:
            raise ValueError("Google ID cannot be empty")
        if self.auth_provider == AuthProviderEnum.google:
            raise ValueError("User is already a Google user")

        self.google_id = google_id
        self.auth_provider = AuthProviderEnum.google
        if profile_picture_url:
            self.profile_picture_url = profile_picture_url

    def deactivate(self) -> None:
        """Deactivate the user."""
        self.is_active = False

    def activate(self) -> None:
        """Activate the user."""
        self.is_active = True

    def promote_to_admin(self) -> None:
        """Promote user to admin role."""
        if RoleEnum.admin not in self.roles:
            self.roles.append(RoleEnum.admin)
        self.token_version += 1  # Invalidate tokens on role change

    def demote_from_admin(self) -> None:
        """Remove admin role from user."""
        if RoleEnum.admin in self.roles:
            self.roles.remove(RoleEnum.admin)
        self.token_version += 1  # Invalidate tokens on role change

    def assert_active(self) -> None:
        """Raise if user is not active."""
        if not self.is_active:
            raise Forbidden(msg="User account is deactivated")

    def assert_local_auth(self) -> None:
        """Raise if user cannot authenticate via local credentials."""
        if self.auth_provider == AuthProviderEnum.google and not self.hashed_password:
            raise Forbidden(msg="Google-only account cannot use local login")

    def has_role(self, role: RoleEnum) -> bool:
        """Check if user has a specific role."""
        return role in self.roles