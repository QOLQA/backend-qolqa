from typing import List

from domain.entities.QueryEntity import QueryEntity
from domain.repositories.query.repo import IQueryRepository


async def get_all_queries(
    repository: IQueryRepository,
) -> List[QueryEntity]:
    """Return all queries in the system."""
    return await repository.get_all()
