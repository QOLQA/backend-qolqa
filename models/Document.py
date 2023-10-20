
from pydantic import BaseModel
from typing import List, Dict


class NestedDoc(BaseModel):
	name: str | None = None
	fields: List[Dict[str, str]] | None = None
	nested_docs: List['NestedDoc'] | None = None


class Relations(BaseModel):
	inner_relations: List[NestedDoc] | None = None
	outer_relations: List[Dict[str, str]] | None = None


class Document(BaseModel):
	name: str | None = None
	fields: List[Dict[str, str]] | None = None
	relations: Relations | None = None





