from typing import List
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from application.dtos.query.QueryRequest import QueryCreateRequest, QueryPartialUpdateRequest
from domain.entities.QueryEntity import QueryEntity
from domain.errors import Missing
from application.repositories.query.repo import IQueryRepository
from infrastructure.mappers import QueryMapper


class QueryRepositoryImpl(IQueryRepository[QueryEntity, QueryCreateRequest, QueryPartialUpdateRequest]):
    """MongoDB implementation of IQueryRepository.

    All DB operations use the QueryMapper — zero inline mapping.
    All domain errors are raised as Missing/Duplicate/etc., never HTTPException.
    """

    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        self.collection = database['queries']
        self.solutions_collection = database['solutions']

    # ------------------------------------------------------------------ #
    # Read                                                                 #
    # ------------------------------------------------------------------ #

    async def get_by_id(self, id: str) -> QueryEntity:
        """Retrieve a query by its string ObjectId."""
        if not ObjectId.is_valid(str(id)):
            raise Missing(msg=f'Invalid query id format: {id}')

        raw = await self.collection.find_one({'_id': ObjectId(str(id))})

        if raw is None:
            raise Missing(msg=f'The query with id: {id} does not exist.')

        return QueryMapper.to_entity_from_dict(raw)

    async def get_all(self) -> List[QueryEntity]:
        """Retrieve all queries."""
        cursor = self.collection.find()
        raws = await cursor.to_list(length=None)
        return [QueryMapper.to_entity_from_dict(raw) for raw in raws]

    async def get_by_solution_id(self, solution_id: str) -> List[QueryEntity]:
        """Retrieve all queries for a given solution."""
        if not ObjectId.is_valid(solution_id):
            raise Missing(msg=f'Invalid solution id format: {solution_id}')

        cursor = self.collection.find({'solution_id': ObjectId(solution_id)})
        raws = await cursor.to_list(length=None)
        return [QueryMapper.to_entity_from_dict(raw) for raw in raws]

    # ------------------------------------------------------------------ #
    # Write                                                                #
    # ------------------------------------------------------------------ #

    async def add(self, entity_create: QueryCreateRequest) -> QueryEntity:
        """Create a new query after verifying the parent solution exists."""
        if not ObjectId.is_valid(entity_create.solution_id):
            raise Missing(msg=f'Invalid solution id format: {entity_create.solution_id}')

        solution = await self.solutions_collection.find_one(
            {'_id': ObjectId(entity_create.solution_id)}
        )
        if solution is None:
            raise Missing(msg=f'The solution with id: {entity_create.solution_id} does not exist.')

        doc = QueryMapper.from_create_request(entity_create)
        result = await self.collection.insert_one(doc)

        return QueryEntity(
            id=str(result.inserted_id),
            full_query=entity_create.full_query,
            collections=entity_create.collections,
            highlighted_words=entity_create.highlighted_words,
            solution_id=entity_create.solution_id,
        )

    async def update(self, id: str, entity_update: QueryPartialUpdateRequest) -> QueryEntity:
        """Partially update a query. Returns the updated entity."""
        if not ObjectId.is_valid(str(id)):
            raise Missing(msg=f'Invalid query id format: {id}')

        update_data = entity_update.model_dump(exclude_unset=True)
        if not update_data:
            # Nothing to change — return current state
            return await self.get_by_id(id)

        result = await self.collection.update_one(
            {'_id': ObjectId(str(id))},
            {'$set': update_data},
        )

        if result.matched_count == 0:
            raise Missing(msg=f'The query with id: {id} does not exist.')

        return await self.get_by_id(id)

    # ------------------------------------------------------------------ #
    # Delete                                                               #
    # ------------------------------------------------------------------ #

    async def delete(self, id: str) -> None:
        """Delete a query by id."""
        if not ObjectId.is_valid(str(id)):
            raise Missing(msg=f'Invalid query id format: {id}')

        result = await self.collection.delete_one({'_id': ObjectId(str(id))})

        if result.deleted_count == 0:
            raise Missing(msg=f'The query with id: {id} does not exist.')

    async def delete_by_solution_id(self, solution_id: str) -> None:
        """Delete all queries belonging to a solution."""
        if not ObjectId.is_valid(solution_id):
            raise Missing(msg=f'Invalid solution id format: {solution_id}')

        await self.collection.delete_many({'solution_id': ObjectId(solution_id)})
