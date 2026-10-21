from domain.repositories.query.repo import IQueryRepository
from domain.repositories.solution.repo import ISolutionRepository


async def delete_queries_by_solution(
    repository: IQueryRepository,
    solution_repository: ISolutionRepository,
    solution_id: str,
    current_user_id: str,
) -> None:
    """Delete all queries belonging to the given solution.

    OWNERSHIP CHECK: raises Forbidden (mapped to 403) when the solution is not
    owned by the current user.
    """
    solution = await solution_repository.get_by_id(solution_id)
    solution.assert_owned_by(current_user_id)

    await repository.delete_by_solution_id(solution_id)
