from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional

# Definir un tipo generico T para representar el modelo
T = TypeVar('T')
TCreate = TypeVar('TCreate')
TUpdate = TypeVar('TUpdate')


class Repository(ABC, Generic[T, TCreate, TUpdate]):
    @abstractmethod
    async def get_by_id(self, id: str | int) -> T:
        '''
        Obtiene un elemento por su ID.
        '''
        pass

    @abstractmethod
    async def add(self, entity_create: TCreate) -> T:
        '''
        Agrega un nuevo elemento al repositorio.
        '''
        pass

    @abstractmethod
    async def get_all(self) -> List[T]:
        '''
        Recupera todos los elementos del repositorio.
        '''
        pass

    @abstractmethod
    async def update(self, id: str | int, entity_update: TUpdate) -> T:
        '''
        Actualiza un elemento existente en el repositorio.
        '''
        pass

    @abstractmethod
    async def delete(self, id: str | int) -> None:
        '''
        Elimina un elemento del repositorio.
        '''
        pass


class IUserRepository(Repository[T, TCreate, TUpdate]):
    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[T]:
        '''
        Obtiene un usuario por su nombre de usuario.
        '''
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[T]:
        '''
        Obtiene un usuario por su email.
        '''
        pass
