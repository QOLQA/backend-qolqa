"""
Auth Commands - Frozen dataclasses for application use cases.
These are agnostic of HTTP/Pydantic and used by use cases.
"""
from dataclasses import dataclass
from typing import List, Optional

from domain.enums.RoleEnum import RoleEnum


@dataclass(frozen=True)
class CreateUserCommand:
    """Command to create a new user."""
    username: str
    email: str
    password: str
    full_name: Optional[str] = None


@dataclass(frozen=True)
class UpdateUserCommand:
    """Command to update user information (self-service)."""
    email: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    profile_picture_url: Optional[str] = None


@dataclass(frozen=True)
class AdminUpdateUserCommand:
    """Command for admin to update any user."""
    email: Optional[str] = None
    full_name: Optional[str] = None
    profile_picture_url: Optional[str] = None
    is_active: Optional[bool] = None
    roles: Optional[List[RoleEnum]] = None


@dataclass(frozen=True)
class RegisterCommand:
    """Command for user registration."""
    username: str
    email: str
    password: str
    full_name: Optional[str] = None


@dataclass(frozen=True)
class AuthenticateCommand:
    """Command to authenticate a user."""
    username: str
    password: str


@dataclass(frozen=True)
class GoogleLoginCommand:
    """Command for Google OAuth login."""
    credential: str
    client_id: Optional[str] = None