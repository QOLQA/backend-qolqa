from application.dtos.version.commands import UpdateVersionCommand
from domain.entities.VersionEntity import VersionEntity
from domain.repositories.solution.repo import ISolutionRepository
from domain.repositories.version.repo import IVersionRepository


async def update_version(
    repository: IVersionRepository,
    solution_repository: ISolutionRepository,
    version_id: str,
    command: UpdateVersionCommand,
    current_user_id: str,
) -> VersionEntity:
    """Partially update a version and return the updated entity.

    OWNERSHIP CHECK: raises Forbidden (mapped to 403) when the solution the
    version belongs to is not owned by the current user. Re-parenting a version
    to another solution requires ownership of that target solution as well.
    """
    entity = await repository.get_by_id(version_id)

    solution = await solution_repository.get_by_id(entity.solution_id)
    solution.assert_owned_by(current_user_id)

    if command.solution_id is not None and command.solution_id != entity.solution_id:
        target_solution = await solution_repository.get_by_id(command.solution_id)
        target_solution.assert_owned_by(current_user_id)
        entity.reparent_to_solution(command.solution_id)

    if command.description is not None:
        entity.update_description(command.description)

    if command.submodels is not None:
        entity.update_submodels(command.submodels)

    return await repository.save(entity)
