from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, field_validator, Field

from config.settings import settings, TypeDB
from models.version import Version

if settings.type_db == TypeDB.mongo:
    from models.base import MongoBaseModel as Base
else: # sql database model
    from models.base import SQLBaseModel as Base

class SolutionBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    last_version_saved: str = Field(default="unknown", max_length=100)
    src_img: str = Field(default="http://unknown.es", max_length=500)
    user_id: str  # Owner of the solution
    last_updated_at: Optional[datetime] = None  # Timestamp of last update
    
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
    last_updated_at: Optional[datetime] = None
    # user_id cannot be updated

class SolutionCreate(BaseModel):
    """Schema for creating a solution - user_id will be added from auth"""
    name: str = Field(min_length=1, max_length=200)
    last_version_saved: str = Field(default="unknown", max_length=100)
    src_img: str = Field(default="http://unknown.es", max_length=500)
    
    @field_validator('name')
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('name cannot be empty')
        return v.strip()

class Solution(Base, SolutionBase):
    versions: List[Version] = []


