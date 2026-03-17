from typing import List, Optional
from datetime import datetime

from pydantic import Field

from domain.entities.VersionEntity import Submodel
from infrastructure.base import MongoBaseModel


class EmbeddedVersion(MongoBaseModel):
    """Embedded version document shape within a solution.

    Mirrors the version collection schema but embedded inside a solution document.
    """

    submodels: List[Submodel] = Field(default=[])
    description: str
    solution_id: str


class SolutionDocument(MongoBaseModel):
    """MongoDB document shape for the 'solutions' collection.

    Inherits `id: PyObjectId` (aliased as `_id`) from MongoBaseModel.
    Versions are embedded as a list.
    """

    name: str = Field(min_length=1, max_length=200)
    user_id: str
    last_version_saved: str = Field(default="unknown", max_length=100)
    src_img: str = Field(default="http://unknown.es", max_length=500)
    last_updated_at: Optional[datetime] = None
    versions: List[EmbeddedVersion] = Field(default=[])
