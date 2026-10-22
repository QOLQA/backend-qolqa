from domain.repositories.query.repo import IQueryRepository
from domain.repositories.solution.repo import ISolutionRepository


async def delete_query(
    repository: IQueryRepository,
    solution_repository: ISolutionRepository,
    query_id: str,
    current_user_id: str,
) -> None:
    """Delete a single query by id.

    OWNERSHIP CHECK: raises Forbidden (mapped to 403) when the solution the
    query belongs to is not owned by the current user.
    """
    entity = await repository.get_by_id(query_id)

    solution = await solution_repository.get_by_id(entity.solution_id)
    solution.assert_owned_by(current_user_id)

    await repository.delete(query_id)
