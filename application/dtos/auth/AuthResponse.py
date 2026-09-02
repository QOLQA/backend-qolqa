from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from domain.enums.RoleEnum import RoleEnum


class UserResponse(BaseModel):
    """DTO for user API responses. Never exposes password or hashed_password."""

    id: str
    username: str
    email: str
    full_name: Optional[str] = None
    is_active: bool
    created_at: datetime
    profile_picture_url: Optional[str] = None
    roles: List[RoleEnum] = []


class TokenResponse(BaseModel):
    """DTO for JWT token API responses."""

    access_token: str
    token_type: str = "bearer"


class GoogleLoginResponse(BaseModel):
    """DTO for Google login API responses. Includes user profile."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse
