from domain.entities.VersionEntity import VersionEntity
from domain.repositories.solution.repo import ISolutionRepository
from domain.repositories.version.repo import IVersionRepository


async def get_version_by_id(
    repository: IVersionRepository,
    solution_repository: ISolutionRepository,
    version_id: str,
    current_user_id: str,
) -> VersionEntity:
    """Return a single version by its id — only if owned by the current user.

    OWNERSHIP CHECK: raises Forbidden (mapped to 403) when the solution the
    version belongs to is not owned by the current user.
    """
    entity = await repository.get_by_id(version_id)

    solution = await solution_repository.get_by_id(entity.solution_id)
    solution.assert_owned_by(current_user_id)

    return entity
