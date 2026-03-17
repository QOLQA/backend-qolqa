from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UserEntity(BaseModel):
    """Pure domain entity for a User. Zero infrastructure dependencies."""

    id: str
    username: str
    email: str
    full_name: Optional[str] = None
    is_active: bool
    created_at: datetime
