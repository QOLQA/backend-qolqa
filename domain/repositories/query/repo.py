from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from domain.entities.QueryEntity import QueryEntity

Entity = TypeVar('Entity', bound=QueryEntity)


class IQueryRepository(ABC, Generic[Entity]):
    """Query repository port (interface)."""

    @abstractmethod
    async def get_by_id(self, id: str) -> Entity | None:
        """Retrieve a query by ID."""
        ...

    @abstractmethod
    async def get_all(self) -> list[Entity]:
        """Retrieve all queries."""
        ...

    @abstractmethod
    async def save(self, entity: Entity) -> Entity:
        """Save (create or update) a query entity."""
        ...

    @abstractmethod
    async def delete(self, id: str) -> None:
        """Delete a query by ID."""
        ...

    @abstractmethod
    async def get_by_solution_id(self, solution_id: str) -> list[Entity]:
        """Retrieve all queries associated with a solution."""
        ...

    @abstractmethod
    async def get_by_solution_ids(self, solution_ids: list[str]) -> list[Entity]:
        """Retrieve all queries belonging to any of the given solutions."""
        ...

    @abstractmethod
    async def delete_by_solution_id(self, solution_id: str) -> None:
        """Delete all queries associated with a solution."""
        ...