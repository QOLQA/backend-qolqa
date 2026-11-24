
from pydantic import Field

from domain.entities.VersionEntity import Submodel

from ..base import MongoBaseModel


class VersionDocument(MongoBaseModel):
    """MongoDB document shape for the 'versions' collection.

    Inherits `id: PyObjectId` (aliased as `_id`) from MongoBaseModel.
    `solution_id` is stored as a plain string in MongoDB (matching
    the existing collection schema observed in repository_nosql.py).
    """

    submodels: list[Submodel] = Field(default=[])
    description: str
    solution_id: str
