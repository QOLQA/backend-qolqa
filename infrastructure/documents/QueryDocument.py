from typing import List

from pydantic import Field

from infrastructure.base import MongoBaseModel, PyObjectId


class QueryDocument(MongoBaseModel):
    """MongoDB document shape for the 'queries' collection.

    Inherits `id: PyObjectId` (aliased as `_id`) from MongoBaseModel.
    `solution_id` is stored as PyObjectId in MongoDB and serialised to str.
    """

    full_query: str
    collections: List[str] = Field(default=[])
    highlighted_words: List[str] = Field(default=[])
    solution_id: PyObjectId = Field(alias="solution_id")
