"""
Auth Commands - Frozen dataclasses for application use cases.
These are agnostic of HTTP/Pydantic and used by use cases.
"""
from dataclasses import dataclass

from domain.enums.RoleEnum import RoleEnum


@dataclass(frozen=True)
class CreateUserCommand:
    """Command to create a new user."""
    username: str
    email: str
    password: str
    full_name: str | None = None


@dataclass(frozen=True)
class UpdateUserCommand:
    """Command to update user information (self-service)."""
    email: str | None = None
    full_name: str | None = None
    is_active: bool | None = None
    profile_picture_url: str | None = None


@dataclass(frozen=True)
class AdminUpdateUserCommand:
    """Command for admin to update any user."""
    email: str | None = None
    full_name: str | None = None
    profile_picture_url: str | None = None
    is_active: bool | None = None
    roles: list[RoleEnum] | None = None


@dataclass(frozen=True)
class RegisterCommand:
    """Command for user registration."""
    username: str
    email: str
    password: str
    full_name: str | None = None


@dataclass(frozen=True)
class AuthenticateCommand:
    """Command to authenticate a user."""
    username: str
    password: str


@dataclass(frozen=True)
class GoogleLoginCommand:
    """Command for Google OAuth login."""
    credential: str
    client_id: str | None = None