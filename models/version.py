from typing import Optional, List
from pydantic import BaseModel

from config.settings import settings, TypeDB

if settings.type_db == TypeDB.mongo:
    from models.base import MongoBaseModel as Base
else: # sql database model
    from models.base import SQLBaseModel as Base

class Query(BaseModel):
    id: str
    full_query: str
    collections: list[str]

class Position(BaseModel):
    x: float
    y: float

class Column(BaseModel):
    id: str
    name: str
    type: str

class NestedNode(BaseModel):
    id: str
    name: str
    cols: List[Column]
    nested_nodes: Optional[List['NestedNode']] = None

class Node(BaseModel):
    id: str
    name: str
    type: str
    position: Position
    cols: List[Column]
    nested_nodes: Optional[List[NestedNode]] = None

class Edge(BaseModel):
    id: str
    source: str
    target: str

class Submodel(BaseModel):
    nodes: List[Node]
    edges: List[Edge]

class VersionBase(BaseModel):
    queries: list[Query]
    submodels: List[Submodel]
    description: str
    solution_id: str

class VersionPartialUpdate(BaseModel):
    queries: Optional[List[Query]] = None
    submodels: Optional[List[Submodel]] = None
    description: Optional[str] = None
    solution_id: Optional[str] = None

class VersionCreate(VersionBase):
    pass

class Version(Base, VersionBase):
    pass

default_version_descriptions = [
    "Primera version",
    "Segunda version",
    "Tercera version",
    "Cuarta version"
]