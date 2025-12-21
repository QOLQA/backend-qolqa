from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from interfaces.repository import Repository
from models.query import Query, QueryCreate, QueryPartialUpdate
from utils.errors import Missing


class QueryRepositoryNoSql(Repository[Query, QueryCreate, QueryPartialUpdate]):
    def __init__(self, database: AsyncIOMotorDatabase):
        self.collection = database['queries']
        self.solutions_collection = database['solutions']

    async def get_by_id(self, id: str | int) -> Query:
        """Get a query by id"""
        if not ObjectId.is_valid(str(id)):
            raise Missing(msg=f'Invalid query id format: {id}')
        
        query_doc = await self.collection.find_one({"_id": ObjectId(str(id))})
        
        if query_doc is None:
            raise Missing(msg=f'The query with id: {id} does not exist.')
        
        return Query(
            id=str(query_doc['_id']),
            full_query=query_doc['full_query'],
            collections=query_doc.get('collections', []),
            solution_id=str(query_doc['solution_id'])
        )
    
    async def get_all(self) -> list[Query]:
        """Get all queries"""
        cursor = self.collection.find()
        queries = await cursor.to_list(length=None)
        
        return [
            Query(
                id=str(query['_id']),
                full_query=query['full_query'],
                collections=query.get('collections', []),
                solution_id=str(query['solution_id'])
            )
            for query in queries
        ]
    
    async def get_by_solution_id(self, solution_id: str) -> list[Query]:
        """Get all queries for a specific solution"""
        if not ObjectId.is_valid(solution_id):
            raise Missing(msg=f'Invalid solution id format: {solution_id}')
        
        cursor = self.collection.find({"solution_id": ObjectId(solution_id)})
        queries = await cursor.to_list(length=None)
        
        return [
            Query(
                id=str(query['_id']),
                full_query=query['full_query'],
                collections=query.get('collections', []),
                solution_id=str(query['solution_id'])
            )
            for query in queries
        ]
    
    async def add(self, entity_data: QueryCreate) -> Query:
        """Create a new query"""
        # Verify solution exists
        if not ObjectId.is_valid(entity_data.solution_id):
            raise Missing(msg=f'Invalid solution id format: {entity_data.solution_id}')
        
        solution = await self.solutions_collection.find_one({"_id": ObjectId(entity_data.solution_id)})
        if solution is None:
            raise Missing(msg=f'The solution with id: {entity_data.solution_id} does not exist.')
        
        # Create query document
        query_doc = {
            "full_query": entity_data.full_query,
            "collections": entity_data.collections,
            "solution_id": ObjectId(entity_data.solution_id)
        }
        
        result = await self.collection.insert_one(query_doc)
        
        return Query(
            id=str(result.inserted_id),
            full_query=entity_data.full_query,
            collections=entity_data.collections,
            solution_id=entity_data.solution_id
        )
    
    async def update(self, id: str | int, entity_data: QueryPartialUpdate) -> Query:
        """Update a query"""
        if not ObjectId.is_valid(str(id)):
            raise Missing(msg=f'Invalid query id format: {id}')
        
        # Build update document with only provided fields
        update_data = entity_data.model_dump(exclude_unset=True)
        if not update_data:
            # No fields to update, just return current query
            return await self.get_by_id(id)
        
        result = await self.collection.update_one(
            {"_id": ObjectId(str(id))},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise Missing(msg=f'The query with id: {id} does not exist.')
        
        return await self.get_by_id(id)
    
    async def delete(self, id: str | int) -> None:
        """Delete a query"""
        if not ObjectId.is_valid(str(id)):
            raise Missing(msg=f'Invalid query id format: {id}')
        
        result = await self.collection.delete_one({"_id": ObjectId(str(id))})
        
        if result.deleted_count == 0:
            raise Missing(msg=f'The query with id: {id} does not exist.')
    
    async def delete_by_solution_id(self, solution_id: str) -> None:
        """Delete all queries for a specific solution"""
        if not ObjectId.is_valid(solution_id):
            raise Missing(msg=f'Invalid solution id format: {solution_id}')
        
        await self.collection.delete_many({"solution_id": ObjectId(solution_id)})
