from application.dtos.solution.SolutionRequest import SolutionCreateRequest
from domain.entities.SolutionEntity import SolutionEntity
from domain.repositories.solution.repo import ISolutionRepository
from infrastructure.mappers.SolutionMapper import SolutionMapper


async def create_solution(
    repository: ISolutionRepository,
    request: SolutionCreateRequest,
    user_id: str,
) -> SolutionEntity:
    """Create a new solution.

    user_id is injected here from the authenticated context and passed to the mapper.
    The mapper is responsible for composing the insertable dict.
    """
    doc = SolutionMapper.from_create_request(request, user_id)
    return await repository.add(doc)
