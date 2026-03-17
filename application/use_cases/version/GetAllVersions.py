from typing import List

from domain.entities.VersionEntity import VersionEntity
from domain.repositories.version.repo import IVersionRepository


async def get_all_versions(
    repository: IVersionRepository,
) -> List[VersionEntity]:
    """Retrieve all versions from the repository."""
    return await repository.get_all()
