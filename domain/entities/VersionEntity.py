from typing import List, Optional
from pydantic import BaseModel, Field


class Position(BaseModel):
    """Value object: 2D coordinates for a node on the canvas."""

    x: float
    y: float


class Column(BaseModel):
    """Value object: a single column inside a node or nested node."""

    id: str
    name: str
    type: str


class NestedNode(BaseModel):
    """Value object: a nested node inside a parent node."""

    id: str
    name: str
    cols: List[Column]
    nested_nodes: Optional[List['NestedNode']] = None
    cardinality: Optional[str] = "1 ... 1"


class Node(BaseModel):
    """Value object: a diagram node with position and optional nested nodes."""

    id: str
    name: str
    type: str
    position: Position
    cols: List[Column]
    nested_nodes: Optional[List[NestedNode]] = None


class Edge(BaseModel):
    """Value object: a directed connection between two nodes."""

    id: str
    source: str
    target: str
    cardinality: Optional[str] = "1 ... 1"


class Submodel(BaseModel):
    """Value object: a logical subgroup of nodes and edges."""

    nodes: List[Node]
    edges: List[Edge]


class VersionEntity(BaseModel):
    """Pure domain entity for a Version. No infrastructure dependencies."""

    id: str = Field(min_length=1)
    submodels: List[Submodel]
    description: str
    solution_id: str = Field(min_length=1)
