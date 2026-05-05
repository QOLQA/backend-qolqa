from typing import List
from pydantic import BaseModel, Field


class QueryResponse(BaseModel):
    """DTO for query API responses. _id is always a plain string (MongoDB convention)."""

    id: str = Field(min_length=1, serialization_alias="_id")
    full_query: str
    collections: List[str]
    highlighted_words: List[str]
    solution_id: str

    class Config:
        populate_by_name = True
