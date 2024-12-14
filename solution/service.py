from models.solution import SolutionCreate, Solution, SolutionPartialUpdate
from utils.get_repository import SolutionRepository

async def get_all(repository: SolutionRepository) -> list[Solution]:
    return await repository.get_all()

async def get_one(repository: SolutionRepository, id: str | int):
    return await repository.get_by_id(id)

async def create(repository: SolutionRepository, solution: SolutionCreate) -> Solution:
    return await repository.add(solution)

async def modify(
    repository: SolutionRepository,
    id: str | int,
    solution_update: SolutionPartialUpdate,
) -> Solution:
    return await repository.update_solution(id, solution_update)

async def delete(
    repository: SolutionRepository,
    id: str | int,
) -> None:
    return await repository.delete(id)
    