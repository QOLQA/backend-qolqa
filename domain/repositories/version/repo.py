from typing import Generic, TypeVar

from domain.repositories.user.repo import Repository

T = TypeVar('T')
TCreate = TypeVar('TCreate')
TUpdate = TypeVar('TUpdate')


class IVersionRepository(Repository[T, TCreate, TUpdate]):
    pass
