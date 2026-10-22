from abc import abstractmethod
from typing import Generic, TypeVar, List

from domain.repositories.user.repo import Repository

T = TypeVar('T')
TCreate = TypeVar('TCreate')
TUpdate = TypeVar('TUpdate')


class IVersionRepository(Repository[T, TCreate, TUpdate]):
    @abstractmethod
    async def get_by_solution_id(self, solution_id: str) -> List[T]:
        '''
        Recupera todas las versiones asociadas a una solución.
        '''
        pass

    @abstractmethod
    async def get_by_solution_ids(self, solution_ids: List[str]) -> List[T]:
        '''
        Recupera todas las versiones asociadas a un conjunto de soluciones.
        '''
        pass

    @abstractmethod
    async def delete_by_solution_id(self, solution_id: str) -> None:
        '''
        Elimina todas las versiones asociadas a una solución.
        '''
        pass
