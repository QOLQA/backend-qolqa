from application.repositories.query.repo import IQueryRepository


async def delete_query(
    repository: IQueryRepository,
    query_id: str,
) -> None:
    """Delete a single query by id."""
    await repository.delete(query_id)
