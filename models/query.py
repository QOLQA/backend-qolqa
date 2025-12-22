from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, ConfigDict

from config.settings import settings, TypeDB

if settings.type_db == TypeDB.mongo:
    from models.base import MongoBaseModel as Base
else:  # sql database model
    from models.base import SQLBaseModel as Base


class QueryBase(BaseModel):
    """Base schema for Query"""
    full_query: str = Field(min_length=1, max_length=10000)
    collections: List[str] = Field(default=[], max_length=50)
    highlighted_words: List[str] = Field(default=[], max_length=50)
    solution_id: str = Field(min_length=1, max_length=100)
    
    @field_validator('full_query')
    @classmethod
    def full_query_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('full_query cannot be empty')
        return v.strip()
    
    @field_validator('solution_id')
    @classmethod
    def solution_id_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('solution_id cannot be empty')
        return v.strip()


class QueryCreate(BaseModel):
    """Schema for creating a query"""
    full_query: str = Field(min_length=1, max_length=10000)
    collections: List[str] = Field(default=[], max_length=50)
    highlighted_words: List[str] = Field(default=[], max_length=50)
    solution_id: str = Field(min_length=1, max_length=100)
    
    @field_validator('full_query')
    @classmethod
    def full_query_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('full_query cannot be empty')
        return v.strip()
    
    @field_validator('solution_id')
    @classmethod
    def solution_id_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('solution_id cannot be empty')
        return v.strip()


class QueryPartialUpdate(BaseModel):
    """Schema for updating a query - all fields optional"""
    full_query: Optional[str] = Field(None, min_length=1, max_length=10000)
    collections: Optional[List[str]] = Field(None, max_length=50)
    highlighted_words: Optional[List[str]] = Field(None, max_length=50)
    # solution_id cannot be updated after creation
    
    @field_validator('full_query')
    @classmethod
    def full_query_must_not_be_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and (not v or not v.strip()):
            raise ValueError('full_query cannot be empty')
        return v.strip() if v else v


class QueryEmbedded(BaseModel):
    """Query model for embedded queries in solutions - uses string id, not ObjectId"""
    id: str = Field(min_length=1, max_length=100, alias="_id")
    full_query: str = Field(min_length=1, max_length=10000)
    collections: List[str] = Field(default=[], max_length=50)
    highlighted_words: List[str] = Field(default=[], max_length=50)
    
    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_serialization_defaults_required=True,
    )
    
    @field_validator('full_query')
    @classmethod
    def full_query_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('full_query cannot be empty')
        return v.strip()


class Query(Base, QueryBase):
    """Complete Query model for queries collection"""
    pass
