from typing import List
from pydantic import BaseModel, Field, field_validator


class QueryEntity(BaseModel):
    """Pure domain entity for a Query. No infrastructure dependencies."""

    id: str = Field(min_length=1)
    full_query: str = Field(min_length=1, max_length=10000)
    collections: List[str] = Field(default=[])
    highlighted_words: List[str] = Field(default=[])
    solution_id: str = Field(min_length=1)

    @field_validator('full_query')
    @classmethod
    def full_query_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('full_query cannot be empty')
        return v.strip()
