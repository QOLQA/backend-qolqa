from datetime import datetime
from typing import List

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from application.dtos.solution.SolutionRequest import SolutionPartialUpdateRequest
from domain.entities.SolutionEntity import SolutionEntity
from domain.errors import Missing
from application.repositories.solution.repo import ISolutionRepository
from infrastructure.mappers import SolutionMapper


class SolutionRepositoryImpl(ISolutionRepository[SolutionEntity, dict, SolutionPartialUpdateRequest]):
    """MongoDB implementation of ISolutionRepository.

    All DB operations use SolutionMapper — zero inline mapping.
    All domain errors are raised as Missing/etc., never HTTPException.
    Versions are stored in a separate 'versions' collection (not embedded).
    """

    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        self.collection = database['solutions']
        self.versions_collection = database['versions']

    # ------------------------------------------------------------------ #
    # Read                                                                 #
    # ------------------------------------------------------------------ #

    async def get_by_id(self, id: str) -> SolutionEntity:
        """Retrieve a solution by its string ObjectId (without versions)."""
        if not ObjectId.is_valid(str(id)):
            raise Missing(msg=f'Invalid solution id format: {id}')

        raw = await self.collection.find_one({'_id': ObjectId(str(id))})

        if raw is None:
            raise Missing(msg=f'The solution with id: {id} does not exist.')

        return SolutionMapper.to_entity(raw)

    async def get_all(self) -> List[SolutionEntity]:
        """Retrieve all solutions (without versions)."""
        cursor = self.collection.find()
        raws = await cursor.to_list(length=None)
        return [SolutionMapper.to_entity(raw) for raw in raws]

    async def get_all_for_user(self, user_id: str) -> List[SolutionEntity]:
        """Retrieve all solutions owned by a specific user.

        CRITICAL: filtering happens at DB level — NOT in Python.
        """
        cursor = self.collection.find({'user_id': user_id})
        raws = await cursor.to_list(length=None)
        return [SolutionMapper.to_entity(raw) for raw in raws]

    # ------------------------------------------------------------------ #
    # Write                                                                #
    # ------------------------------------------------------------------ #

    async def add(self, entity_create: dict) -> SolutionEntity:
        """Insert a new solution document.

        Expects a MongoDB-insertable dict (produced by SolutionMapper.from_create_request).
        """
        result = await self.collection.insert_one(entity_create)
        return await self.get_by_id(result.inserted_id)

    async def update(self, id: str, entity_update: SolutionPartialUpdateRequest) -> SolutionEntity:
        """Partially update a solution. Returns the updated entity."""
        if not ObjectId.is_valid(str(id)):
            raise Missing(msg=f'Invalid solution id format: {id}')

        update_data = entity_update.model_dump(exclude_unset=True)

        # Always stamp the update time
        update_data['last_updated_at'] = datetime.utcnow()

        result = await self.collection.update_one(
            {'_id': ObjectId(str(id))},
            {'$set': update_data},
        )

        if result.matched_count == 0:
            raise Missing(msg=f'The solution with id: {id} does not exist.')

        return await self.get_by_id(id)

    # ------------------------------------------------------------------ #
    # Delete                                                               #
    # ------------------------------------------------------------------ #

    async def delete(self, id: str) -> None:
        """Delete a solution by id."""
        if not ObjectId.is_valid(str(id)):
            raise Missing(msg=f'Invalid solution id format: {id}')

        result = await self.collection.delete_one({'_id': ObjectId(str(id))})

        if result.deleted_count == 0:
            raise Missing(msg=f'The solution with id: {id} does not exist.')
