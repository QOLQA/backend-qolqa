from typing import List

from domain.entities.QueryEntity import QueryEntity
from application.repositories.query.repo import IQueryRepository


async def get_queries_by_solution(
    repository: IQueryRepository,
    solution_id: str,
) -> List[QueryEntity]:
    """Return all queries associated with the given solution id."""
    return await repository.get_by_solution_id(solution_id)
