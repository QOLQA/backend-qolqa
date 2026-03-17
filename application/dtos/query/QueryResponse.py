from typing import List
from pydantic import BaseModel, Field


class QueryResponse(BaseModel):
    """DTO for query API responses. id is always a plain string."""

    id: str = Field(min_length=1)
    full_query: str
    collections: List[str]
    highlighted_words: List[str]
    solution_id: str
