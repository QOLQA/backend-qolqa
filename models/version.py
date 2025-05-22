from typing import Any, Optional
from pydantic import BaseModel

from config.settings import settings, TypeDB

if settings.type_db == TypeDB.mongo:
    from models.base import MongoBaseModel as Base
else: # sql database model
    from models.base import SQLBaseModel as Base

class Query(BaseModel):
    full_query: str
    collections: list[str]

class VersionBase(BaseModel):
    queries: list[Query]
    submodels: Any
    description: str
    solution_id: str

class VersionPartialUpdate(BaseModel):
    queries: Optional[list[Query]] = None
    submodels: Optional[Any] = None
    description: Optional[str] = None
    solution_id: Optional[str] = None

class VersionCreate(VersionBase):
    pass

class Version(Base, VersionBase):
    pass