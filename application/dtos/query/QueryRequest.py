from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class QueryCreateRequest(BaseModel):
    """DTO for creating a new query."""

    full_query: str = Field(min_length=1, max_length=10000)
    collections: List[str] = Field(default=[], max_length=50)
    highlighted_words: List[str] = Field(default=[], max_length=50)
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

    full_query: Optional[str] = Field(None, min_length=1, max_length=10000)
    collections: Optional[List[str]] = Field(None, max_length=50)
    highlighted_words: Optional[List[str]] = Field(None, max_length=50)
    # solution_id is intentionally excluded — cannot be updated after creation

    @field_validator('full_query')
    @classmethod
    def full_query_must_not_be_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and (not v or not v.strip()):
            raise ValueError('full_query cannot be empty')
        return v.strip() if v else v
