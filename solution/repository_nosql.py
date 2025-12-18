from motor.motor_asyncio import AsyncIOMotorDatabase

from interfaces.repository import Repository

from models.solution import Solution, SolutionCreate, SolutionPartialUpdate
from utils.mongo import get_object_id
from utils.errors import Missing
from utils.db_timeout import with_timeout


class SolutionRepositoryNoSql(Repository[Solution, SolutionCreate, SolutionPartialUpdate]):
    def __init__(self, database: AsyncIOMotorDatabase):
        self.database = database

    async def get_by_id(self, id):
        object_id = await get_object_id(id)

        raw_solution = await with_timeout(
            self.database['solutions'].find_one,
            {'_id': object_id},
            operation_name=f"get solution by id {id}"
        )
        
        if raw_solution is None:
            raise Missing(msg=f'The solution with _id: {id} does not exists.')
        
        return Solution(**raw_solution)
    
    async def add(self, entity_data):
        solution_created = await with_timeout(
            self.database['solutions'].insert_one,
            entity_data.model_dump(),
            operation_name="insert solution"
        )
        
        return await self.get_by_id(solution_created.inserted_id)
    
    async def get_all(self):
        # Note: For find() with cursor, we don't wrap with timeout at the query level
        # Instead, we use max_time_ms directly in MongoDB
        query = self.database['solutions'].find({}).max_time_ms(10000)  # 10 second timeout

        results = [
            Solution(**raw_solution)
            async for raw_solution in query
        ]

        return results
    
    async def update(self, id, entity_update):
        solution = await self.get_by_id(id)
        
        await with_timeout(
            self.database['solutions'].update_one,
            {'_id': solution.id},
            {'$set': entity_update.model_dump(exclude_unset=True)},
            operation_name=f"update solution {id}"
        )
        
        solution = await self.get_by_id(id)

        return solution
    
    async def delete(self, id):
        solution = await self.get_by_id(id)

        await with_timeout(
            self.database['solutions'].delete_one,
            {'_id': solution.id},
            operation_name=f"delete solution {id}"
        )
