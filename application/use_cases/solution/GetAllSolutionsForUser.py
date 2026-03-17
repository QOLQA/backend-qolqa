from typing import List

from domain.entities.SolutionEntity import SolutionEntity
from domain.repositories.solution.repo import ISolutionRepository


async def get_all_solutions_for_user(
    repository: ISolutionRepository,
    user_id: str,
) -> List[SolutionEntity]:
    """Return all solutions owned by a given user.

    Ownership filtering happens at DB level inside the repository — NOT in Python.
    """
    return await repository.get_all_for_user(user_id)
