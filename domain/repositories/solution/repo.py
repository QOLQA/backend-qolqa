from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional

from domain.entities.SolutionEntity import SolutionEntity

Entity = TypeVar('Entity', bound=SolutionEntity)


class ISolutionRepository(ABC, Generic[Entity]):
    """Solution repository port (interface)."""

    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[Entity]:
        """Retrieve a solution by ID."""
        ...

    @abstractmethod
    async def get_all(self) -> List[Entity]:
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
    async def get_all_for_user(self, user_id: str) -> List[Entity]:
        """Retrieve all solutions owned by a user."""
        ...