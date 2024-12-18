from models.solution import SolutionCreate, Solution, SolutionPartialUpdate
from interfaces.repository import Repository

async def get_all(repository: Repository) -> list[Solution]:
    return await repository.get_all()

async def get_one(repository: Repository, id: str | int):
    return await repository.get_by_id(id)

async def create(repository: Repository, solution: SolutionCreate) -> Solution:
    return await repository.add(solution)

async def modify(
    repository: Repository,
    id: str | int,
    solution_update: SolutionPartialUpdate,
) -> Solution:
    return await repository.update(id, solution_update)

async def delete(
    repository: Repository,
    id: str | int,
) -> None:
    return await repository.delete(id)
    