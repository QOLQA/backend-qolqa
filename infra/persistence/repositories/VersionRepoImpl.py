
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from domain.entities.VersionEntity import VersionEntity
from domain.errors import Missing
from domain.repositories.version.repo import IVersionRepository

from ..mappers import VersionMapper


class VersionRepositoryImpl(IVersionRepository[VersionEntity]):
    """MongoDB implementation of IVersionRepository.

    All DB operations use VersionMapper — zero inline mapping.
    All domain errors are raised as Missing/etc., never HTTPException.
    """

    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        self.collection = database['versions']
        self.solutions_collection = database['solutions']

    # ------------------------------------------------------------------ #
    # Read                                                                 #
    # ------------------------------------------------------------------ #

    async def get_by_id(self, id: str) -> VersionEntity:
        """Retrieve a version by its string ObjectId."""
        if not ObjectId.is_valid(str(id)):
            raise Missing(msg=f'Invalid version id format: {id}')

        raw = await self.collection.find_one({'_id': ObjectId(str(id))})

        if raw is None:
            raise Missing(msg=f'The version with id: {id} does not exist.')

        return VersionMapper.to_entity(raw)

    async def get_all(self) -> list[VersionEntity]:
        """Retrieve all versions."""
        cursor = self.collection.find()
        raws = await cursor.to_list(length=None)
        return [VersionMapper.to_entity(raw) for raw in raws]

    async def get_by_solution_id(self, solution_id: str) -> list[VersionEntity]:
        """Retrieve all versions for a given solution."""
        cursor = self.collection.find({'solution_id': solution_id})
        raws = await cursor.to_list(length=None)
        return [VersionMapper.to_entity(raw) for raw in raws]

    async def get_by_solution_ids(self, solution_ids: list[str]) -> list[VersionEntity]:
        """Retrieve all versions belonging to any of the given solutions.

        `versions.solution_id` is stored as a plain string, so the ids are used
        as-is in the query (no ObjectId conversion).
        """
        ids = [str(solution_id) for solution_id in solution_ids]

        if not ids:
            return []

        cursor = self.collection.find({'solution_id': {'$in': ids}})
        raws = await cursor.to_list(length=None)
        return [VersionMapper.to_entity(raw) for raw in raws]

    # ------------------------------------------------------------------ #
    # Write                                                                #
    # ------------------------------------------------------------------ #

    async def save(self, entity: VersionEntity) -> VersionEntity:
        """Save (create or update) a version entity."""
        if not entity.id or not ObjectId.is_valid(entity.id):
            # New entity - verify parent solution exists
            if not ObjectId.is_valid(entity.solution_id):
                raise Missing(msg=f'Invalid solution id format: {entity.solution_id}')

            solution = await self.solutions_collection.find_one(
                {'_id': ObjectId(entity.solution_id)}
            )
            if solution is None:
                raise Missing(msg=f'The solution with id: {entity.solution_id} does not exist.')

        doc = VersionMapper.to_persistence(entity)

        await self.collection.update_one(
            {'_id': ObjectId(entity.id)} if entity.id and ObjectId.is_valid(entity.id) else {'solution_id': entity.solution_id, 'description': entity.description},
            {'$set': doc},
            upsert=True,
        )

        # Re-fetch
        return await self.get_by_id(entity.id)

    async def delete(self, id: str) -> None:
        """Delete a version by id."""
        if not ObjectId.is_valid(str(id)):
            raise Missing(msg=f'Invalid version id format: {id}')

        result = await self.collection.delete_one({'_id': ObjectId(str(id))})

        if result.deleted_count == 0:
            raise Missing(msg=f'The version with id: {id} does not exist.')

    async def delete_by_solution_id(self, solution_id: str) -> None:
        """Delete all versions belonging to a solution."""
        await self.collection.delete_many({'solution_id': solution_id})