from datetime import datetime
from typing import List, Optional

from pydantic import Field

from domain.enums.AuthProviderEnum import AuthProviderEnum
from domain.enums.RoleEnum import RoleEnum
from infrastructure.base import MongoBaseModel


class UserDocument(MongoBaseModel):
    """MongoDB document shape for the 'users' collection.

    Inherits `id: PyObjectId` (aliased as `_id`) from MongoBaseModel.
    """

    username: str
    email: str
    full_name: Optional[str] = None
    is_active: bool = True
    hashed_password: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    profile_picture_url: Optional[str] = None
    roles: List[RoleEnum] = Field(default_factory=list)
    token_version: int = Field(default=0)
    google_id: Optional[str] = None
    auth_provider: AuthProviderEnum = AuthProviderEnum.local
