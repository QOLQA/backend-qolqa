from application.dtos.query.QueryRequest import QueryPartialUpdateRequest
from domain.entities.QueryEntity import QueryEntity
from domain.repositories.query.repo import IQueryRepository
from domain.repositories.solution.repo import ISolutionRepository


async def update_query(
    repository: IQueryRepository,
    solution_repository: ISolutionRepository,
    query_id: str,
    request: QueryPartialUpdateRequest,
    current_user_id: str,
) -> QueryEntity:
    """Partially update a query and return the updated entity.

    OWNERSHIP CHECK: raises Forbidden (mapped to 403) when the solution the
    query belongs to is not owned by the current user.
    """
    entity = await repository.get_by_id(query_id)

    solution = await solution_repository.get_by_id(entity.solution_id)
    solution.assert_owned_by(current_user_id)

    if request.full_query is not None:
        entity.update_query(request.full_query)

    if request.collections is not None:
        entity.update_collections(request.collections)

    if request.highlighted_words is not None:
        entity.update_highlighted_words(request.highlighted_words)

    return await repository.save(entity)
