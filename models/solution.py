from typing import Any
from pydantic import BaseModel

from config.settings import settings, TypeDB

if settings.type_db == TypeDB.mongo:
    from models.base import MongoBaseModel as Base
else: # sql database model
    from models.base import SQLBaseModel as Base

class Query(BaseModel):
    full_query: str
    collections: list[str]

class SolutionBase(BaseModel):
    name: str
    submodels: Any
    queries: list[Query]

class SolutionPartialUpdate(BaseModel):
    name: str | None = None
    submodels: Any | None = None
    queries: list[Query] | None = None

class SolutionCreate(SolutionBase):
    pass

class Solution(Base, SolutionBase):
    pass


