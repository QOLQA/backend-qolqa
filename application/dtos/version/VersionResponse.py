from typing import List
from pydantic import BaseModel, Field

from domain.entities.VersionEntity import Submodel, Node, Edge


class VersionResponse(BaseModel):
    """DTO for version API responses. id is always a plain string."""

    id: str = Field(min_length=1, serialization_alias='_id')
    submodels: List[Submodel]
    description: str
    solution_id: str
