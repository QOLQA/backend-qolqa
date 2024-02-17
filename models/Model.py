
from pydantic import BaseModel, UUID4
from typing import List, Dict


class NestedDoc(BaseModel):
	name: str | None = None
	fields: Dict[str, str] | None = None
	nested_docs: List['NestedDoc'] | None = None

class Position(BaseModel):
    x: int
    y: int

class Document(BaseModel):
	name: str | None = None
	id: str
	fields: Dict[str, str] | None = None
	position: Position
	nested_docs: List[NestedDoc] | None


class SubModel(BaseModel):
  documents: List[Document]
  relations: Dict[str, str] | None
  
  
class Model(BaseModel):
  submodels: List[SubModel]


