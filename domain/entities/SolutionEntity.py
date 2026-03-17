from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from domain.entities.VersionEntity import VersionEntity


class SolutionEntity(BaseModel):
    """Pure domain entity for a Solution. No infrastructure dependencies."""

    id: str = Field(min_length=1)
    name: str = Field(min_length=1, max_length=200)
    user_id: str = Field(min_length=1)
    last_version_saved: str = Field(default="unknown", max_length=100)
    src_img: str = Field(default="http://unknown.es", max_length=500)
    last_updated_at: Optional[datetime] = None
    versions: List[VersionEntity] = []
