from typing import Optional, List
from pydantic import BaseModel, field_validator, Field

from config.settings import settings, TypeDB
from models.version import Version

if settings.type_db == TypeDB.mongo:
    from models.base import MongoBaseModel as Base
else: # sql database model
    from models.base import SQLBaseModel as Base

class Query(BaseModel):
    id: str = Field(default='', max_length=100)
    full_query: str = Field(default='', max_length=10000)
    collections: List[str] = Field(default=[], max_length=50)

class SolutionBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    last_version_saved: str = Field(default="unknown", max_length=100)
    src_img: str = Field(default="http://unknown.es", max_length=500)
    queries: List[Query] = Field(default=[], max_length=100)
    user_id: str  # Owner of the solution
    
    @field_validator('name')
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('name cannot be empty')
        return v.strip()

class SolutionPartialUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    last_version_saved: Optional[str] = Field(None, max_length=100)
    src_img: Optional[str] = Field(None, max_length=500)
    queries: Optional[List[Query]] = None
    # user_id cannot be updated

class SolutionCreate(BaseModel):
    """Schema for creating a solution - user_id will be added from auth"""
    name: str = Field(min_length=1, max_length=200)
    last_version_saved: str = Field(default="unknown", max_length=100)
    src_img: str = Field(default="http://unknown.es", max_length=500)
    queries: List[Query] = Field(default=[], max_length=100)
    
    @field_validator('name')
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('name cannot be empty')
        return v.strip()

class Solution(Base, SolutionBase):
    versions: List[Version] = []

class Solution(Base, SolutionBase):
    versions: List[Version] = []


