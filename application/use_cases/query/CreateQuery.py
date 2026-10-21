from application.dtos.query.QueryRequest import QueryCreateRequest
from domain.entities.QueryEntity import QueryEntity
from domain.repositories.query.repo import IQueryRepository
from domain.repositories.solution.repo import ISolutionRepository


async def create_query(
    repository: IQueryRepository,
    solution_repository: ISolutionRepository,
    request: QueryCreateRequest,
    current_user_id: str,
) -> QueryEntity:
    """Create a new query and return the persisted entity.

    OWNERSHIP CHECK: raises Forbidden (mapped to 403) when the target solution
    is not owned by the current user.
    """
    solution = await solution_repository.get_by_id(request.solution_id)
    solution.assert_owned_by(current_user_id)

    return await repository.add(request)
