from domain.entities.QueryEntity import QueryEntity
from domain.repositories.query.repo import IQueryRepository
from domain.repositories.solution.repo import ISolutionRepository


async def get_query_by_id(
    repository: IQueryRepository,
    solution_repository: ISolutionRepository,
    query_id: str,
    current_user_id: str,
) -> QueryEntity:
    """Return a single query by its id — only if owned by the current user.

    OWNERSHIP CHECK: raises Forbidden (mapped to 403) when the solution the
    query belongs to is not owned by the current user.
    """
    entity = await repository.get_by_id(query_id)

    solution = await solution_repository.get_by_id(entity.solution_id)
    solution.assert_owned_by(current_user_id)

    return entity
