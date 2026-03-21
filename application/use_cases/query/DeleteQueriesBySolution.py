from application.repositories.query.repo import IQueryRepository


async def delete_queries_by_solution(
    repository: IQueryRepository,
    solution_id: str,
) -> None:
    """Delete all queries belonging to the given solution."""
    await repository.delete_by_solution_id(solution_id)
