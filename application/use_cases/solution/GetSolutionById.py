from typing import List

from domain.entities.SolutionEntity import SolutionEntity
from domain.entities.VersionEntity import VersionEntity
from domain.repositories.solution.repo import ISolutionRepository


async def get_solution_by_id(
    repository: ISolutionRepository,
    solution_id: str,
    versions: List[VersionEntity] = None,
) -> SolutionEntity:
    """Retrieve a solution by id.

    Optionally accepts pre-fetched versions to attach to the returned entity.
    The caller (controller) is responsible for fetching versions via the version repository.
    """
    entity = await repository.get_by_id(solution_id)

    if versions is not None:
        entity.versions = versions

    return entity
