from typing import List

from domain.entities.VersionEntity import VersionEntity
from domain.repositories.solution.repo import ISolutionRepository
from domain.repositories.version.repo import IVersionRepository


async def get_all_versions(
    repository: IVersionRepository,
    solution_repository: ISolutionRepository,
    user_id: str,
) -> List[VersionEntity]:
    """Return all versions owned by the given user.

    Ownership filtering happens at DB level: the user's own solutions are
    resolved first and only the versions attached to them are returned.
    """
    solutions = await solution_repository.get_all_for_user(user_id)

    if not solutions:
        return []

    return await repository.get_by_solution_ids([solution.id for solution in solutions])
