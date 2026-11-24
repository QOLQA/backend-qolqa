from bson import ObjectId

from application.dtos.query.commands import CreateQueryCommand
from domain.entities.QueryEntity import QueryEntity
from domain.repositories.query.repo import IQueryRepository
from domain.repositories.solution.repo import ISolutionRepository


async def create_query(
    repository: IQueryRepository,
    solution_repository: ISolutionRepository,
    command: CreateQueryCommand,
) -> QueryEntity:
    """Create a new query and return the persisted entity.

    OWNERSHIP CHECK: raises Forbidden (mapped to 403) when the target solution
    is not owned by the current user.
    """
    solution = await solution_repository.get_by_id(command.solution_id)
    solution.assert_owned_by(command.current_user_id)

    entity = QueryEntity.create(
        id=str(ObjectId()),
        full_query=command.full_query,
        solution_id=command.solution_id,
        collections=command.collections,
        highlighted_words=command.highlighted_words,
    )

    return await repository.save(entity)
