from fastapi import APIRouter, HTTPException, status, Depends
from bson import ObjectId, errors
from motor.motor_asyncio import AsyncIOMotorDatabase

from config.mongo import get_database
from models.solution import SolutionCreate, Solution, SolutionPartialUpdate

router = APIRouter()

async def get_object_id(id: str) -> ObjectId:
    try:
        return ObjectId(id)
    except (errors.InvalidId, TypeError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    
async def get_solution_or_404(
    id: ObjectId = Depends(get_object_id),
    database: AsyncIOMotorDatabase = Depends(get_database),
) -> Solution:
    raw_solution = await database['solutions'].find_one({'_id': id})

    if raw_solution is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    
    return Solution(**raw_solution)


@router.get("/", response_model=list[Solution])
async def all(
    database: AsyncIOMotorDatabase = Depends(get_database),
) -> list[Solution]:
    query = database['solutions'].find({})

    results = [Solution(**raw_solution) async for raw_solution in query]

    return results


@router.get("/{id}", response_model=Solution)
async def get(
    solution: Solution = Depends(get_solution_or_404),
) -> Solution:
    return solution


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=Solution)
async def create(
    solution_create: SolutionCreate,
    database: AsyncIOMotorDatabase = Depends(get_database),
) -> Solution:
    solution = Solution(**solution_create.model_dump())
    await database['solutions'].insert_one(solution.model_dump(by_alias=True))

    solution = await get_solution_or_404(solution.id, database)

    return solution

@router.patch('/{id}', response_model=Solution)
async def update(
    solution_update: SolutionPartialUpdate,
    solution: Solution = Depends(get_solution_or_404),
    database: AsyncIOMotorDatabase = Depends(get_database),
) -> Solution:
    await database['solutions'].update_one(
        {'_id': solution.id},
        {'$set': solution_update.model_dump(exclude_unset=True)}
    )

    solution = await get_solution_or_404(solution.id, database)

    return solution

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    solution: Solution = Depends(get_solution_or_404),
    database: AsyncIOMotorDatabase = Depends(get_database),
) -> None:
    await database['solutions'].delete_one({'_id': solution.id})
    