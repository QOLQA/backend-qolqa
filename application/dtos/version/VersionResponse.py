from typing import List
from pydantic import BaseModel, Field

from domain.entities.VersionEntity import Submodel


class VersionResponse(BaseModel):
    """DTO for version API responses. _id is always a plain string (MongoDB convention)."""

    id: str = Field(min_length=1, serialization_alias="_id")
    submodels: List[Submodel]
    description: str
    solution_id: str

    class Config:
        populate_by_name = True
