from domain.entities.QueryEntity import QueryEntity
from domain.repositories.query.repo import IQueryRepository


async def get_query_by_id(
    repository: IQueryRepository,
    query_id: str,
) -> QueryEntity:
    """Return a single query by its id."""
    return await repository.get_by_id(query_id)
