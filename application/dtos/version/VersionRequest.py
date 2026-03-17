from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

from domain.entities.VersionEntity import Submodel


class VersionCreateRequest(BaseModel):
    """DTO for creating a new version."""

    submodels: List[Submodel] = Field(default=[])
    description: str = Field(min_length=1, max_length=500)
    solution_id: str = Field(min_length=1, max_length=100)

    @field_validator('description')
    @classmethod
    def description_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('description cannot be empty')
        return v.strip()

    @field_validator('solution_id')
    @classmethod
    def solution_id_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('solution_id cannot be empty')
        return v.strip()


class VersionPartialUpdateRequest(BaseModel):
    """DTO for partially updating a version. All fields are optional."""

    submodels: Optional[List[Submodel]] = None
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    solution_id: Optional[str] = Field(None, min_length=1, max_length=100)

    @field_validator('description')
    @classmethod
    def description_must_not_be_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and (not v or not v.strip()):
            raise ValueError('description cannot be empty')
        return v.strip() if v else v
