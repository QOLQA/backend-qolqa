from typing import Optional
from pydantic import BaseModel

from config.settings import settings, TypeDB
from models.version import Version

if settings.type_db == TypeDB.mongo:
    from models.base import MongoBaseModel as Base
else: # sql database model
    from models.base import SQLBaseModel as Base

class Query(BaseModel):
    id: str = ''
    full_query: str = ''
    collections: list[str] = []

class SolutionBase(BaseModel):
    name: str
    last_version_saved: str = "unknown"
    src_img: str = "http://unknown.es"
    queries: list[Query] = []

class SolutionPartialUpdate(BaseModel):
    name: Optional[str] = None
    last_version_saved: Optional[str] = None
    src_img: Optional[str] = None
    queries: Optional[list[Query]] = None

class SolutionCreate(SolutionBase):
    pass

class Solution(Base, SolutionBase):
    versions: list[Version] = []


