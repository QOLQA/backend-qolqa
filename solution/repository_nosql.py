from motor.motor_asyncio import AsyncIOMotorDatabase

from interfaces.repository import Repository

from models.solution import Solution, SolutionCreate, SolutionPartialUpdate
from utils.mongo import get_object_id
from utils.errors import Missing


class SolutionRepositoryNoSql(Repository[Solution, SolutionCreate, SolutionPartialUpdate]):
    def __init__(self, database: AsyncIOMotorDatabase):
        self.database = database

    async def get_by_id(self, id):
        object_id = await get_object_id(id)

        raw_solution = await self.database['solutions'] \
            .find_one({'_id': object_id})
        
        if raw_solution is None:
            raise Missing(msg=f'The solution with _id: {id} does not exists.')
        
        return Solution(**raw_solution)
    
    async def add(self, entity_data):
        solution_created = await self.database['solutions'] \
            .insert_one(entity_data.model_dump())
        
        return await self.get_by_id(solution_created.inserted_id)
    
    async def get_all(self):
        query = self.database['solutions'].find({})

        results = [
            Solution(**raw_solution)
            async for raw_solution in query
        ]

        return results
    
    async def update(self, id, entity_update):
        solution = await self.get_by_id(id)
        
        await self.database['solutions'] \
            .update_one(
                {'_id': solution.id},
                {'$set': entity_update.model_dump(exclude_unset=True)}
            )
        
        solution = await self.get_by_id(id)

        return solution
    
    async def delete(self, id):
        solution = await self.get_by_id(id)

        await self.database['solutions'] \
            .delete_one({'_id': solution.id})
