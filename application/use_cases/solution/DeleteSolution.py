from domain.errors import Forbidden
from domain.repositories.solution.repo import ISolutionRepository
from domain.repositories.version.repo import IVersionRepository
from motor.motor_asyncio import AsyncIOMotorDatabase


async def delete_solution(
    solution_repository: ISolutionRepository,
    solution_id: str,
    current_user_id: str,
    version_repository: IVersionRepository = None,
    query_repository=None,
    database: AsyncIOMotorDatabase = None,
) -> None:
    """Delete a solution and all its associated versions and queries.

    OWNERSHIP CHECK: raises Forbidden (mapped to 403) if the current user does not own this solution.

    Cascade deletes (in transaction when database is provided):
    - All versions belonging to the solution (if version_repository provided)
    - All queries belonging to the solution (if query_repository provided)
    - The solution itself
    """
    entity = await solution_repository.get_by_id(solution_id)

    if entity.user_id != current_user_id:
        raise Forbidden(
            msg=f'User {current_user_id} is not authorized to delete solution {solution_id}.'
        )

    # If database is provided (MongoDB), run cascade in a transaction
    if database is not None:
        client = database.client
        async with await client.start_session() as session:
            async with session.start_transaction():
                if query_repository is not None:
                    await query_repository.delete_by_solution_id(solution_id)

                if version_repository is not None:
                    await version_repository.delete_by_solution_id(solution_id)

                await solution_repository.delete(solution_id)
    else:
        # No transaction (e.g., tests with mocks)
        if query_repository is not None:
            await query_repository.delete_by_solution_id(solution_id)

        if version_repository is not None:
            await version_repository.delete_by_solution_id(solution_id)

        await solution_repository.delete(solution_id)
