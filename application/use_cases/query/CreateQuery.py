from application.dtos.query.QueryRequest import QueryCreateRequest
from domain.entities.QueryEntity import QueryEntity
from application.repositories.query.repo import IQueryRepository


async def create_query(
    repository: IQueryRepository,
    request: QueryCreateRequest,
) -> QueryEntity:
    """Create a new query and return the persisted entity."""
    return await repository.add(request)
