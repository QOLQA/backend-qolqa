from application.dtos.solution.SolutionRequest import SolutionPartialUpdateRequest
from domain.entities.SolutionEntity import SolutionEntity
from domain.errors import Forbidden
from domain.repositories.solution.repo import ISolutionRepository


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

    if request.name is not None:
        entity.update_name(request.name)

    if request.last_version_saved is not None:
        entity.update_last_version(request.last_version_saved)

    if request.src_img is not None:
        entity.update_image(request.src_img)

    return await repository.save(entity)
