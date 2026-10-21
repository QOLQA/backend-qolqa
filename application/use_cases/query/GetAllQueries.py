from typing import List

from domain.entities.QueryEntity import QueryEntity
from domain.repositories.query.repo import IQueryRepository
from domain.repositories.solution.repo import ISolutionRepository


async def get_all_queries(
    repository: IQueryRepository,
    solution_repository: ISolutionRepository,
    user_id: str,
) -> List[QueryEntity]:
    """Return all queries owned by the given user.

    Ownership filtering happens at DB level: the user's own solutions are
    resolved first and only the queries attached to them are returned.
    """
    solutions = await solution_repository.get_all_for_user(user_id)

    if not solutions:
        return []

    return await repository.get_by_solution_ids([solution.id for solution in solutions])
