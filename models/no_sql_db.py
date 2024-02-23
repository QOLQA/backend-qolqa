from pydantic import BaseModel
from typing import List, Dict


class NestedCollection(BaseModel):
	name: str | None = None
	fields: Dict[str, str] | None = None
	nested_docs: List['NestedCollection'] | None = None

class Position(BaseModel):
    x: int
    y: int

class Collection(BaseModel):
	name: str | None = None
	id: str
	fields: Dict[str, str] | None = None
	position: Position
	nested_docs: List[NestedCollection] | None


class SubModel(BaseModel):
  documents: List[Collection]
  relations: Dict[str, str] | None
  
  
class NoSqlDBForm(BaseModel):
  submodels: List[SubModel]
  
class NoSqlDB(NoSqlDBForm):
  id: str
