from typing import List

from domain.entities.QueryEntity import QueryEntity
from domain.repositories.query.repo import IQueryRepository
from domain.repositories.solution.repo import ISolutionRepository


async def get_queries_by_solution(
    repository: IQueryRepository,
    solution_repository: ISolutionRepository,
    solution_id: str,
    current_user_id: str,
) -> List[QueryEntity]:
    """Return all queries associated with the given solution id.

    OWNERSHIP CHECK: raises Forbidden (mapped to 403) when the solution is not
    owned by the current user.
    """
    solution = await solution_repository.get_by_id(solution_id)
    solution.assert_owned_by(current_user_id)

    return await repository.get_by_solution_id(solution_id)
