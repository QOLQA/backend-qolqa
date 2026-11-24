from datetime import datetime

from pydantic import Field

from domain.enums.AuthProviderEnum import AuthProviderEnum
from domain.enums.RoleEnum import RoleEnum

from ..base import MongoBaseModel


class UserDocument(MongoBaseModel):
    """MongoDB document shape for the 'users' collection.

    Inherits `id: PyObjectId` (aliased as `_id`) from MongoBaseModel.
    """

    username: str
    email: str
    full_name: str | None = None
    is_active: bool = True
    hashed_password: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    profile_picture_url: str | None = None
    roles: list[RoleEnum] = Field(default_factory=list)
    token_version: int = Field(default=0)
    google_id: str | None = None
    auth_provider: AuthProviderEnum = AuthProviderEnum.local
