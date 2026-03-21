from typing import List

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from application.dtos.version.VersionRequest import VersionCreateRequest, VersionPartialUpdateRequest
from domain.entities.VersionEntity import VersionEntity
from domain.errors import Missing
from application.repositories.version.repo import IVersionRepository
from infrastructure.mappers import VersionMapper


class VersionRepositoryImpl(IVersionRepository[VersionEntity, VersionCreateRequest, VersionPartialUpdateRequest]):
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

    async def get_all(self) -> List[VersionEntity]:
        """Retrieve all versions."""
        cursor = self.collection.find()
        raws = await cursor.to_list(length=None)
        return [VersionMapper.to_entity(raw) for raw in raws]

    async def get_by_solution_id(self, solution_id: str) -> List[VersionEntity]:
        """Retrieve all versions for a given solution."""
        cursor = self.collection.find({'solution_id': solution_id})
        raws = await cursor.to_list(length=None)
        return [VersionMapper.to_entity(raw) for raw in raws]

    # ------------------------------------------------------------------ #
    # Write                                                                #
    # ------------------------------------------------------------------ #

    async def add(self, entity_create: VersionCreateRequest) -> VersionEntity:
        """Create a new version after verifying the parent solution exists."""
        if not ObjectId.is_valid(entity_create.solution_id):
            raise Missing(msg=f'Invalid solution id format: {entity_create.solution_id}')

        solution = await self.solutions_collection.find_one(
            {'_id': ObjectId(entity_create.solution_id)}
        )
        if solution is None:
            raise Missing(msg=f'The solution with id: {entity_create.solution_id} does not exist.')

        doc = VersionMapper.from_create_request(entity_create)
        result = await self.collection.insert_one(doc)

        return VersionEntity(
            id=str(result.inserted_id),
            submodels=entity_create.submodels,
            description=entity_create.description,
            solution_id=entity_create.solution_id,
        )

    async def update(self, id: str, entity_update: VersionPartialUpdateRequest) -> VersionEntity:
        """Partially update a version. Returns the updated entity."""
        if not ObjectId.is_valid(str(id)):
            raise Missing(msg=f'Invalid version id format: {id}')

        update_data = entity_update.model_dump(exclude_unset=True)
        if not update_data:
            # Nothing to change — return current state
            return await self.get_by_id(id)

        # Serialize submodels to dicts if present
        if 'submodels' in update_data and update_data['submodels'] is not None:
            update_data['submodels'] = [
                s.model_dump() if hasattr(s, 'model_dump') else s
                for s in update_data['submodels']
            ]

        result = await self.collection.update_one(
            {'_id': ObjectId(str(id))},
            {'$set': update_data},
        )

        if result.matched_count == 0:
            raise Missing(msg=f'The version with id: {id} does not exist.')

        return await self.get_by_id(id)

    # ------------------------------------------------------------------ #
    # Delete                                                               #
    # ------------------------------------------------------------------ #

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
