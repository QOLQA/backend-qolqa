from application.dtos.version.VersionRequest import VersionCreateRequest
from domain.entities.VersionEntity import VersionEntity
from domain.repositories.solution.repo import ISolutionRepository
from domain.repositories.version.repo import IVersionRepository


async def create_version(
    repository: IVersionRepository,
    solution_repository: ISolutionRepository,
    request: VersionCreateRequest,
    current_user_id: str,
) -> VersionEntity:
    """Create a new version and return the persisted entity.

    OWNERSHIP CHECK: raises Forbidden (mapped to 403) when the target solution
    is not owned by the current user.
    """
    solution = await solution_repository.get_by_id(request.solution_id)
    solution.assert_owned_by(current_user_id)

    return await repository.add(request)
