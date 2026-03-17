from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from domain.repositories.user.repo import Repository
from models.query import Query, QueryCreate, QueryPartialUpdate
from schemas.solution import Query as QueryDB, Solution as SolutionDB
from utils.sql import get_integer_id
from domain.errors import Missing


class QueryRepositorySql(Repository[Query, QueryCreate, QueryPartialUpdate]):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: str | int) -> Query:
        """Get a query by id"""
        integer_id = await get_integer_id(id)
        select_query = select(QueryDB).where(QueryDB.id == integer_id)
        
        result = await self.session.execute(select_query)
        query = result.scalar_one_or_none()

        if query is None:
            raise Missing(msg=f'The query with id: {id} does not exist.')
        
        return Query(
            _id=str(query.id),
            full_query=query.full_query,
            collections=query.collections,
            highlighted_words=query.highlighted_words,
            solution_id=str(query.solution_id)
        )
    
    async def get_all(self) -> list[Query]:
        """Get all queries"""
        select_query = select(QueryDB)
        result = await self.session.execute(select_query)
        queries = result.scalars().all()
        
        return [
            Query(
                _id=str(query.id),
                full_query=query.full_query,
                collections=query.collections,
                highlighted_words=query.highlighted_words,
                solution_id=str(query.solution_id)
            )
            for query in queries
        ]
    
    async def get_by_solution_id(self, solution_id: str) -> list[Query]:
        """Get all queries for a specific solution"""
        integer_solution_id = await get_integer_id(solution_id)
        select_query = select(QueryDB).where(QueryDB.solution_id == integer_solution_id)
        
        result = await self.session.execute(select_query)
        queries = result.scalars().all()
        
        return [
            Query(
                _id=str(query.id),
                full_query=query.full_query,
                collections=query.collections,
                highlighted_words=query.highlighted_words,
                solution_id=str(query.solution_id)
            )
            for query in queries
        ]
    
    async def add(self, entity_data: QueryCreate) -> Query:
        """Create a new query"""
        # Verify solution exists
        integer_solution_id = await get_integer_id(entity_data.solution_id)
        solution_query = select(SolutionDB).where(SolutionDB.id == integer_solution_id)
        result = await self.session.execute(solution_query)
        solution = result.scalar_one_or_none()
        
        if solution is None:
            raise Missing(msg=f'The solution with id: {entity_data.solution_id} does not exist.')
        
        # Create query
        query = QueryDB(
            full_query=entity_data.full_query,
            collections=entity_data.collections,
            highlighted_words=entity_data.highlighted_words,
            solution_id=integer_solution_id
        )
        
        self.session.add(query)
        await self.session.commit()
        await self.session.refresh(query)
        
        return Query(
            _id=str(query.id),
            full_query=query.full_query,
            collections=query.collections,
            highlighted_words=query.highlighted_words,
            solution_id=str(query.solution_id)
        )
    
    async def update(self, id: str | int, entity_data: QueryPartialUpdate) -> Query:
        """Update a query"""
        integer_id = await get_integer_id(id)
        select_query = select(QueryDB).where(QueryDB.id == integer_id)
        
        result = await self.session.execute(select_query)
        query = result.scalar_one_or_none()

        if query is None:
            raise Missing(msg=f'The query with id: {id} does not exist.')
        
        # Update only provided fields
        update_data = entity_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(query, key, value)
        
        await self.session.commit()
        await self.session.refresh(query)
        
        return Query(
            _id=str(query.id),
            full_query=query.full_query,
            collections=query.collections,
            highlighted_words=query.highlighted_words,
            solution_id=str(query.solution_id)
        )
    
    async def delete(self, id: str | int) -> None:
        """Delete a query"""
        integer_id = await get_integer_id(id)
        select_query = select(QueryDB).where(QueryDB.id == integer_id)
        
        result = await self.session.execute(select_query)
        query = result.scalar_one_or_none()

        if query is None:
            raise Missing(msg=f'The query with id: {id} does not exist.')
        
        await self.session.delete(query)
        await self.session.commit()
    
    async def delete_by_solution_id(self, solution_id: str) -> None:
        """Delete all queries for a specific solution"""
        integer_solution_id = await get_integer_id(solution_id)
        delete_query = delete(QueryDB).where(QueryDB.solution_id == integer_solution_id)
        
        await self.session.execute(delete_query)
        await self.session.commit()
