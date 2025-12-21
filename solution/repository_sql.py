from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from interfaces.repository import Repository

from models.solution import Solution, SolutionCreate, SolutionPartialUpdate
from schemas.solution import Solution as SolutionDB
from utils.sql import get_integer_id
from utils.errors import Missing

class SolutionRepositorySql(Repository[Solution, SolutionCreate, SolutionPartialUpdate]):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id):
        integer_id = await get_integer_id(id)
        select_query = (select(SolutionDB)
            .where(SolutionDB.id == integer_id))
        
        result = await self.session.execute(select_query)

        solution = result.scalar_one_or_none()

        if solution is None:
            raise Missing(msg=f'The solution with id: {id} does not exists.')
        
        return solution
    
    async def add(self, entity_data):
        solution = SolutionDB(**entity_data.model_dump())
        
        self.session.add(solution)
        await self.session.commit()

        return await self.get_by_id(solution.id)
    
    async def get_all(self):
        select_query = select(SolutionDB)
        
        result = await self.session.execute(select_query)

        return result.scalars().all()
    
    async def delete(self, id):
        solution = await self.get_by_id(id)
        await self.session.delete(solution)
        await self.session.commit()
        
    async def update(self, id, entity_update):
        solution_update_dict = entity_update.model_dump(exclude_unset=True)
        solution = await self.get_by_id(id)
        for key, value in solution_update_dict.items():
            setattr(solution, key, value)

        self.session.add(solution)
        await self.session.commit()

        return solution