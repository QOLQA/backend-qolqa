from abc import abstractmethod
from typing import Generic, TypeVar, List

from application.repositories.user.repo import Repository

T = TypeVar('T')
TCreate = TypeVar('TCreate')
TUpdate = TypeVar('TUpdate')


class ISolutionRepository(Repository[T, TCreate, TUpdate]):
    @abstractmethod
    async def get_all_for_user(self, user_id: str) -> List[T]:
        '''
        Recupera todas las soluciones pertenecientes a un usuario.
        '''
        pass
