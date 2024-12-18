from fastapi import APIRouter, Depends, status

from models.solution import Solution, SolutionCreate, SolutionPartialUpdate
from solution import service
from solution.repository_nosql import SolutionRepositoryNoSql

from utils.handle_errors import handle_common_errors
from utils.get_database import get_database

router = APIRouter()


@router.get('', response_model=list[Solution])
async def all(
    database = Depends(get_database),
) -> list[Solution]:
    return await service.get_all(SolutionRepositoryNoSql(database))


@router.post('', response_model=Solution, status_code=status.HTTP_201_CREATED)
async def create(
    solution_create: SolutionCreate,
    database = Depends(get_database),
) -> Solution:
    try:
        return await service.create(SolutionRepositoryNoSql(database), solution_create)
    except Exception as exc:
        await handle_common_errors(exc)


@router.get('/{id}', response_model=Solution)
async def get(
    id: int | str,
    database = Depends(get_database),
) -> Solution:
    try:
        return await service.get_one(SolutionRepositoryNoSql(database), id)
    except Exception as exc:
        await handle_common_errors(exc)


@router.patch('/{id}', response_model=Solution)
async def update(
    id: str | int,
    solution_update: SolutionPartialUpdate,
    database = Depends(get_database),
) -> Solution:
    try:
        return await service.modify(SolutionRepositoryNoSql(database), id, solution_update)
    except Exception as exc:
        await handle_common_errors(exc)
    

@router.delete('/{id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    id: str | int,
    database = Depends(get_database),
) -> None:
    try:
        return await service.delete(SolutionRepositoryNoSql(database), id)
    except Exception as exc:
        await handle_common_errors(exc)
