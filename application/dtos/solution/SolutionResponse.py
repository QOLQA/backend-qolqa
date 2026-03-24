from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from application.dtos.version.VersionResponse import VersionResponse


class SolutionResponse(BaseModel):
    """DTO for solution API responses. id is always a plain string."""

    id: str = Field(min_length=1, serialization_alias='_id')
    name: str
    user_id: str
    last_version_saved: str
    src_img: str
    last_updated_at: Optional[datetime] = None
    versions: List[VersionResponse] = []
