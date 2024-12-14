from fastapi import APIRouter, Depends, status, Query

from interfaces.repository import Repository
from models.solution import Solution, SolutionCreate, SolutionPartialUpdate
from solution import service

from utils.handle_errors import handle_common_errors
from utils.get_repository import get_repository

router = APIRouter()


@router.get('', response_model=list[Solution])
async def all(
    repository: Repository = Depends(get_repository),
    name: str = Query(default=None)
) -> list[Solution]:
    if name is None:
        return await service.get_all(repository)
    return await service.get_one_by_name(repository, name)


@router.post('', response_model=Solution, status_code=status.HTTP_201_CREATED)
async def create(
    solution_create: SolutionCreate,
    repository: Repository = Depends(get_repository),
) -> Solution:
    try:
        return await service.create(repository, solution_create)
    except Exception as exc:
        await handle_common_errors(exc)


@router.get('/{id}', response_model=Solution)
async def get(
    id: int | str,
    repository: Repository = Depends(get_repository),
) -> Solution:
    try:
        return await service.get_one(repository, id)
    except Exception as exc:
        await handle_common_errors(exc)


@router.patch('/{id}', response_model=Solution)
async def update(
    id: str | int,
    solution_update: SolutionPartialUpdate,
    repository: Repository = Depends(get_repository),
) -> Solution:
    try:
        return await service.modify(repository, id, solution_update)
    except Exception as exc:
        await handle_common_errors(exc)
    

@router.delete('/{id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    id: str | int,
    repository: Repository = Depends(get_repository),
) -> None:
    try:
        return await service.delete(repository, id)
    except Exception as exc:
        await handle_common_errors(exc)
