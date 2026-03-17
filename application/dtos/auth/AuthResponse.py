from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UserResponse(BaseModel):
    """DTO for user API responses. Never exposes password or hashed_password."""

    id: str
    username: str
    email: str
    full_name: Optional[str] = None
    is_active: bool
    created_at: datetime


class TokenResponse(BaseModel):
    """DTO for JWT token API responses."""

    access_token: str
    token_type: str = "bearer"
