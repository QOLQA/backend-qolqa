from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional

from domain.entities.VersionEntity import VersionEntity

Entity = TypeVar('Entity', bound=VersionEntity)


class IVersionRepository(ABC, Generic[Entity]):
    """Version repository port (interface)."""

    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[Entity]:
        """Retrieve a version by ID."""
        ...

    @abstractmethod
    async def get_all(self) -> List[Entity]:
        """Retrieve all versions."""
        ...

    @abstractmethod
    async def save(self, entity: Entity) -> Entity:
        """Save (create or update) a version entity."""
        ...

    @abstractmethod
    async def delete(self, id: str) -> None:
        """Delete a version by ID."""
        ...

    @abstractmethod
    async def get_by_solution_id(self, solution_id: str) -> List[Entity]:
        """Retrieve all versions associated with a solution."""
        ...

    @abstractmethod
    async def get_by_solution_ids(self, solution_ids: List[str]) -> List[Entity]:
        """Retrieve all versions associated with a set of solutions."""
        ...

    @abstractmethod
    async def delete_by_solution_id(self, solution_id: str) -> None:
        """Delete all versions associated with a solution."""
        ...