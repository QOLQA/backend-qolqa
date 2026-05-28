from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from domain.enums.RoleEnum import RoleEnum


class UserCreateRequest(BaseModel):
    """DTO for creating a new user. Includes password strength validators."""

    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=100)
    full_name: Optional[str] = Field(None, max_length=100)

    @field_validator('username')
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        """Validate username contains only alphanumeric characters and underscores."""
        if not v.replace('_', '').isalnum():
            raise ValueError('Username must contain only letters, numbers, and underscores')
        return v.lower()

    @field_validator('password')
    @classmethod
    def password_strength(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserLoginRequest(BaseModel):
    """DTO for user login."""

    username: str
    password: str


class UserUpdateRequest(BaseModel):
    """DTO for updating user information."""

    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None
    profile_picture_url: Optional[str] = None


class AdminUserUpdateRequest(BaseModel):
    """DTO for admin updating any user. Includes roles and is_active."""

    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=100)
    profile_picture_url: Optional[str] = None
    is_active: Optional[bool] = None
    roles: Optional[List[RoleEnum]] = None
