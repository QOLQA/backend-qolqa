from models.query import QueryCreate, Query, QueryPartialUpdate
from domain.repositories.user.repo import Repository


async def get_all(repository: Repository) -> list[Query]:
    """Get all queries"""
    return await repository.get_all()


async def get_one(repository: Repository, id: str | int) -> Query:
    """Get a single query by id"""
    return await repository.get_by_id(id)


async def get_by_solution(repository: Repository, solution_id: str) -> list[Query]:
    """Get all queries for a specific solution"""
    return await repository.get_by_solution_id(solution_id)


async def create(repository: Repository, query: QueryCreate) -> Query:
    """Create a new query"""
    return await repository.add(query)


async def modify(
    repository: Repository,
    id: str | int,
    query_update: QueryPartialUpdate,
) -> Query:
    """Update an existing query"""
    return await repository.update(id, query_update)


async def delete(repository: Repository, id: str | int) -> None:
    """Delete a query"""
    return await repository.delete(id)


async def delete_by_solution(repository: Repository, solution_id: str) -> None:
    """Delete all queries for a specific solution"""
    return await repository.delete_by_solution_id(solution_id)
