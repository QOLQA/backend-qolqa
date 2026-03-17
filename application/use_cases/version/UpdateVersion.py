from application.dtos.version.VersionRequest import VersionPartialUpdateRequest
from domain.entities.VersionEntity import VersionEntity
from domain.repositories.version.repo import IVersionRepository


async def update_version(
    repository: IVersionRepository,
    version_id: str,
    request: VersionPartialUpdateRequest,
) -> VersionEntity:
    """Partially update a version and return the updated entity."""
    return await repository.update(version_id, request)
