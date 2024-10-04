from typing import Any
from pydantic import BaseModel

import models.base as base

class Query(BaseModel):
    full_query: str
    collections: list[str]

class SolutionBase(base.MongoBaseModel):
    name: str
    submodels: Any
    queries: list[Query]

class SolutionPartialUpdate(BaseModel):
    name: str | None = None
    submodels: Any | None = None
    queries: list[Query] | None = None

class SolutionCreate(SolutionBase):
    pass

class Solution(SolutionBase):
    pass


