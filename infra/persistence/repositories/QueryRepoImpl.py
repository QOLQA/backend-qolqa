
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from domain.entities.QueryEntity import QueryEntity
from domain.errors import Missing
from domain.repositories.query.repo import IQueryRepository

from ..mappers import QueryMapper


class QueryRepositoryImpl(IQueryRepository[QueryEntity]):
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

    async def get_all(self) -> list[QueryEntity]:
        """Retrieve all queries."""
        cursor = self.collection.find()
        raws = await cursor.to_list(length=None)
        return [QueryMapper.to_entity_from_dict(raw) for raw in raws]

    async def get_by_solution_id(self, solution_id: str) -> list[QueryEntity]:
        """Retrieve all queries for a given solution."""
        if not ObjectId.is_valid(solution_id):
            raise Missing(msg=f'Invalid solution id format: {solution_id}')

        cursor = self.collection.find({'solution_id': ObjectId(solution_id)})
        raws = await cursor.to_list(length=None)
        return [QueryMapper.to_entity_from_dict(raw) for raw in raws]

    async def get_by_solution_ids(self, solution_ids: list[str]) -> list[QueryEntity]:
        """Retrieve all queries belonging to any of the given solutions.

        `queries.solution_id` is stored as an ObjectId, so every id is converted
        before being used in the query. Invalid ids are skipped.
        """
        oids = []
        for solution_id in solution_ids:
            if ObjectId.is_valid(str(solution_id)):
                oids.append(ObjectId(str(solution_id)))

        if not oids:
            return []

        cursor = self.collection.find({'solution_id': {'$in': oids}})
        raws = await cursor.to_list(length=None)
        return [QueryMapper.to_entity_from_dict(raw) for raw in raws]

    # ------------------------------------------------------------------ #
    # Write                                                                #
    # ------------------------------------------------------------------ #

    async def save(self, entity: QueryEntity) -> QueryEntity:
        """Save (create or update) a query entity."""
        if not entity.id or not ObjectId.is_valid(entity.id):
            # New entity - verify parent solution exists
            if not ObjectId.is_valid(entity.solution_id):
                raise Missing(msg=f'Invalid solution id format: {entity.solution_id}')

            solution = await self.solutions_collection.find_one(
                {'_id': ObjectId(entity.solution_id)}
            )
            if solution is None:
                raise Missing(msg=f'The solution with id: {entity.solution_id} does not exist.')

        doc = QueryMapper.to_persistence(entity)

        await self.collection.update_one(
            {'_id': ObjectId(entity.id)} if entity.id and ObjectId.is_valid(entity.id) else {'solution_id': ObjectId(entity.solution_id), 'full_query': entity.full_query},
            {'$set': doc},
            upsert=True,
        )

        # Re-fetch
        return await self.get_by_id(entity.id)

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