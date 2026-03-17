from domain.entities.VersionEntity import VersionEntity
from domain.repositories.version.repo import IVersionRepository


async def get_version_by_id(
    repository: IVersionRepository,
    version_id: str,
) -> VersionEntity:
    """Retrieve a single version by its id."""
    return await repository.get_by_id(version_id)
