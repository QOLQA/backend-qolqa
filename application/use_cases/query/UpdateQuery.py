from application.dtos.query.QueryRequest import QueryPartialUpdateRequest
from domain.entities.QueryEntity import QueryEntity
from domain.repositories.query.repo import IQueryRepository


async def update_query(
    repository: IQueryRepository,
    query_id: str,
    request: QueryPartialUpdateRequest,
) -> QueryEntity:
    """Partially update a query and return the updated entity."""
    return await repository.update(query_id, request)
