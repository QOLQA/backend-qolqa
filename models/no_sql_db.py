from pydantic import BaseModel
from typing import List, Dict


class NestedCollection(BaseModel):
  name: str | None = None
  fields: Dict[str, str] | None = None
  nested_docs: List['NestedCollection'] | None = None
  id: str
  cardinality: str | None = None

class Position(BaseModel):
  x: int
  y: int

class Collection(BaseModel):
	name: str | None = None
	id: str
	fields: Dict[str, str] | None = None
	position: Position
	nested_docs: List[NestedCollection] | None
 
class Relation(BaseModel):
  id_source: str
  id_target: str
  cardinality: str | None = None

class SubModel(BaseModel):
  collections: List[Collection]
  relations: list[Relation] | None = None
  
class Query(BaseModel):
  full_query: str
  collections: list[str]
  
class NoSqlDBForm(BaseModel):
  submodels: List[SubModel]
  name: str
  queries: list[Query] = []
  
class NoSqlDB(NoSqlDBForm):
  id: str
