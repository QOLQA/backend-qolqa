from application.dtos.version.VersionRequest import VersionPartialUpdateRequest
from domain.entities.VersionEntity import VersionEntity
from domain.repositories.solution.repo import ISolutionRepository
from domain.repositories.version.repo import IVersionRepository


async def update_version(
    repository: IVersionRepository,
    solution_repository: ISolutionRepository,
    version_id: str,
    request: VersionPartialUpdateRequest,
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

    if request.solution_id is not None and request.solution_id != entity.solution_id:
        target_solution = await solution_repository.get_by_id(request.solution_id)
        target_solution.assert_owned_by(current_user_id)

    return await repository.update(version_id, request)
