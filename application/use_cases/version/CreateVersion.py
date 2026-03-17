from application.dtos.version.VersionRequest import VersionCreateRequest
from domain.entities.VersionEntity import VersionEntity
from domain.repositories.version.repo import IVersionRepository


async def create_version(
    repository: IVersionRepository,
    request: VersionCreateRequest,
) -> VersionEntity:
    """Create a new version and return the persisted entity."""
    return await repository.add(request)
