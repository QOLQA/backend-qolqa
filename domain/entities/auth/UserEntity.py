from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from domain.enums.RoleEnum import RoleEnum


class UserEntity(BaseModel):
    """Pure domain entity for a User. Zero infrastructure dependencies."""

    id: str
    username: str
    email: str
    full_name: Optional[str] = None
    is_active: bool
    created_at: datetime
    profile_picture_url: Optional[str] = None
    roles: List[RoleEnum] = Field(default_factory=list)
    token_version: int = 0
