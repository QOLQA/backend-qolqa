from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from application.dtos.version.VersionResponse import VersionResponse


class SolutionResponse(BaseModel):
    """DTO for solution API responses. _id is always a plain string (MongoDB convention)."""

    id: str = Field(min_length=1, serialization_alias="_id")
    name: str
    user_id: str
    last_version_saved: str
    src_img: str
    last_updated_at: Optional[datetime] = None
    versions: List[VersionResponse] = []

    class Config:
        populate_by_name = True
