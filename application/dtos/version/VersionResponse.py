from typing import List
from pydantic import BaseModel, Field

from domain.entities.VersionEntity import Submodel


class VersionResponse(BaseModel):
    """DTO for version API responses. id is always a plain string."""

    id: str = Field(min_length=1)
    submodels: List[Submodel]
    description: str
    solution_id: str
