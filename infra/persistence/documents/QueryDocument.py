
from pydantic import Field

from ..base import MongoBaseModel, PyObjectId


class QueryDocument(MongoBaseModel):
    """MongoDB document shape for the 'queries' collection.

    Inherits `id: PyObjectId` (aliased as `_id`) from MongoBaseModel.
    `solution_id` is stored as PyObjectId in MongoDB and serialised to str.
    """

    full_query: str
    collections: list[str] = Field(default=[])
    highlighted_words: list[str] = Field(default=[])
    solution_id: PyObjectId = Field(alias="solution_id")
