from application.dtos.version.commands import CreateVersionCommand
from domain.entities.VersionEntity import VersionEntity
from domain.repositories.solution.repo import ISolutionRepository
from domain.repositories.version.repo import IVersionRepository
from bson import ObjectId


async def create_version(
    repository: IVersionRepository,
    solution_repository: ISolutionRepository,
    command: CreateVersionCommand,
) -> VersionEntity:
    """Create a new version and return the persisted entity.

    OWNERSHIP CHECK: raises Forbidden (mapped to 403) when the target solution
    is not owned by the current user.
    """
    solution = await solution_repository.get_by_id(command.solution_id)
    solution.assert_owned_by(command.current_user_id)

    entity = VersionEntity.create(
        id=str(ObjectId()),
        submodels=command.submodels,
        description=command.description,
        solution_id=command.solution_id,
    )

    return await repository.save(entity)
