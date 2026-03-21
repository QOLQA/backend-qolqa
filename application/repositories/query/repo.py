from abc import abstractmethod
from typing import Generic, TypeVar, List

from application.repositories.user.repo import Repository

T = TypeVar('T')
TCreate = TypeVar('TCreate')
TUpdate = TypeVar('TUpdate')


class IQueryRepository(Repository[T, TCreate, TUpdate]):
    @abstractmethod
    async def get_by_solution_id(self, solution_id: str) -> List[T]:
        '''
        Recupera todas las queries asociadas a una solución.
        '''
        pass

    @abstractmethod
    async def delete_by_solution_id(self, solution_id: str) -> None:
        '''
        Elimina todas las queries asociadas a una solución.
        '''
        pass
