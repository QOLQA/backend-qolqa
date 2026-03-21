from application.dtos.solution.SolutionRequest import SolutionPartialUpdateRequest
from domain.entities.SolutionEntity import SolutionEntity
from domain.errors import Forbidden
from application.repositories.solution.repo import ISolutionRepository


async def update_solution(
    repository: ISolutionRepository,
    solution_id: str,
    request: SolutionPartialUpdateRequest,
    current_user_id: str,
) -> SolutionEntity:
    """Partially update a solution.

    OWNERSHIP CHECK: raises Missing (mapped to 403 by the controller) if the
    current user does not own this solution.
    """
    entity = await repository.get_by_id(solution_id)

    if entity.user_id != current_user_id:
        raise Forbidden(
            msg=f'User {current_user_id} is not authorized to modify solution {solution_id}.'
        )

    return await repository.update(solution_id, request)
