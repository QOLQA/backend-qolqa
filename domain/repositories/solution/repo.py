from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from domain.entities.SolutionEntity import SolutionEntity

Entity = TypeVar('Entity', bound=SolutionEntity)


class ISolutionRepository(ABC, Generic[Entity]):
    """Solution repository port (interface)."""

    @abstractmethod
    async def get_by_id(self, id: str) -> Entity | None:
        """Retrieve a solution by ID."""
        ...

    @abstractmethod
    async def get_all(self) -> list[Entity]:
        """Retrieve all solutions."""
        ...

    @abstractmethod
    async def save(self, entity: Entity) -> Entity:
        """Save (create or update) a solution entity."""
        ...

    @abstractmethod
    async def delete(self, id: str) -> None:
        """Delete a solution by ID."""
        ...

    @abstractmethod
    async def get_all_for_user(self, user_id: str) -> list[Entity]:
        """Retrieve all solutions owned by a user."""
        ...