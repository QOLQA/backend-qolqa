
from pydantic import BaseModel, Field, field_validator


class QueryCreateRequest(BaseModel):
    """DTO for creating a new query."""

    full_query: str = Field(min_length=1, max_length=10000)
    collections: list[str] = Field(default=[], max_length=50)
    highlighted_words: list[str] = Field(default=[], max_length=50)
    solution_id: str = Field(min_length=1, max_length=100)

    @field_validator('full_query')
    @classmethod
    def full_query_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('full_query cannot be empty')
        return v.strip()

    @field_validator('solution_id')
    @classmethod
    def solution_id_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('solution_id cannot be empty')
        return v.strip()


class QueryPartialUpdateRequest(BaseModel):
    """DTO for partially updating a query. All fields are optional."""

    full_query: str | None = Field(None, min_length=1, max_length=10000)
    collections: list[str] | None = Field(None, max_length=50)
    highlighted_words: list[str] | None = Field(None, max_length=50)
    # solution_id is intentionally excluded — cannot be updated after creation

    @field_validator('full_query')
    @classmethod
    def full_query_must_not_be_empty(cls, v: str | None) -> str | None:
        if v is not None and (not v or not v.strip()):
            raise ValueError('full_query cannot be empty')
        return v.strip() if v else v
