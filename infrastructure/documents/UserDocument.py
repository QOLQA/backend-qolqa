from datetime import datetime
from typing import Optional

from pydantic import Field

from infrastructure.base import MongoBaseModel


class UserDocument(MongoBaseModel):
    """MongoDB document shape for the 'users' collection.

    Inherits `id: PyObjectId` (aliased as `_id`) from MongoBaseModel.
    """

    username: str
    email: str
    full_name: Optional[str] = None
    is_active: bool = True
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
