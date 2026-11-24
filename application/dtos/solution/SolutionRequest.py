
from pydantic import BaseModel, Field, field_validator


class SolutionCreateRequest(BaseModel):
    """DTO for creating a new solution. user_id is injected from auth, NOT provided by client."""

    name: str = Field(min_length=1, max_length=200)
    last_version_saved: str = Field(default="unknown", max_length=100)
    src_img: str = Field(default="http://unknown.es", max_length=500)

    @field_validator('name')
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('name cannot be empty')
        return v.strip()


class SolutionPartialUpdateRequest(BaseModel):
    """DTO for partially updating a solution. All fields are optional. user_id cannot be updated."""

    name: str | None = Field(None, min_length=1, max_length=200)
    last_version_saved: str | None = Field(None, max_length=100)
    src_img: str | None = Field(None, max_length=500)

    @field_validator('name')
    @classmethod
    def name_must_not_be_empty(cls, v: str | None) -> str | None:
        if v is not None and (not v or not v.strip()):
            raise ValueError('name cannot be empty')
        return v.strip() if v else v
