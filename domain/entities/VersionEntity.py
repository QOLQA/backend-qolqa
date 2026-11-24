from dataclasses import dataclass, field


@dataclass
class Position:
    """Value object: 2D coordinates for a node on the canvas."""

    x: float
    y: float


@dataclass
class Column:
    """Value object: a single column inside a node or nested node."""

    id: str
    name: str
    type: str


@dataclass
class NestedNode:
    """Value object: a nested node inside a parent node."""

    id: str
    name: str
    cols: list[Column]
    nested_nodes: list['NestedNode'] | None = None
    cardinality: str = "1 ... 1"


@dataclass
class Node:
    """Value object: a diagram node with position and optional nested nodes."""

    id: str
    name: str
    type: str
    position: Position
    cols: list[Column]
    nested_nodes: list[NestedNode] | None = None


@dataclass
class Edge:
    """Value object: a directed connection between two nodes."""

    id: str
    source: str
    target: str
    cardinality: str = "1 ... 1"


@dataclass
class Submodel:
    """Value object: a logical subgroup of nodes and edges."""

    nodes: list[Node] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)


@dataclass
class VersionEntity:
    """Pure domain entity for a Version. No infrastructure dependencies."""

    id: str
    submodels: list[Submodel]
    description: str
    solution_id: str

    # ------------------------------------------------------------------ #
    # Factory Methods
    # ------------------------------------------------------------------ #

    @classmethod
    def create(
        cls,
        id: str,
        submodels: list[Submodel],
        description: str,
        solution_id: str,
    ) -> "VersionEntity":
        """Create a new version."""
        if not id:
            raise ValueError("Version ID is required")
        if not solution_id:
            raise ValueError("Solution ID is required")
        if not description or not description.strip():
            raise ValueError("Description cannot be empty")
        if submodels is None:
            raise ValueError("Submodels list is required")

        return cls(
            id=id,
            submodels=submodels,
            description=description.strip(),
            solution_id=solution_id,
        )

    # ------------------------------------------------------------------ #
    # Business Mutation Methods
    # ------------------------------------------------------------------ #

    def update_description(self, description: str) -> None:
        """Update version description."""
        if not description or not description.strip():
            raise ValueError("Description cannot be empty")
        self.description = description.strip()

    def update_submodels(self, submodels: list[Submodel]) -> None:
        """Replace all submodels."""
        if submodels is None:
            raise ValueError("Submodels list is required")
        self.submodels = submodels

    def add_submodel(self, submodel: Submodel) -> None:
        """Add a submodel."""
        if not submodel:
            raise ValueError("Submodel cannot be None")
        self.submodels.append(submodel)

    def remove_submodel(self, index: int) -> bool:
        """Remove a submodel by index. Returns True if removed."""
        if 0 <= index < len(self.submodels):
            self.submodels.pop(index)
            return True
        return False

    def reparent_to_solution(self, new_solution_id: str) -> None:
        """Change the parent solution ID."""
        if not new_solution_id:
            raise ValueError("Solution ID cannot be empty")
        self.solution_id = new_solution_id