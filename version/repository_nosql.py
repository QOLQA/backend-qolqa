from motor.motor_asyncio import AsyncIOMotorDatabase

from interfaces.repository import Repository
from models.version import Version, VersionCreate, VersionPartialUpdate
from utils.mongo import get_object_id
from utils.errors import Missing


class VersionRepositoryNoSql(Repository[Version, VersionCreate, VersionPartialUpdate]):
    def __init__(self, database: AsyncIOMotorDatabase):
        self.database = database

    async def get_by_id(self, id):
        object_id = await get_object_id(id)

        raw_version = await self.database['versions'] \
            .find_one({'_id': object_id})
        
        if raw_version is None:
            raise Missing(msg=f'The version with _id: {id} does not exist.')
        
        return Version(**raw_version)
    
    async def add(self, entity_data):
        version_created = await self.database['versions'] \
            .insert_one(entity_data.model_dump())
        
        return await self.get_by_id(version_created.inserted_id)
    
    async def get_all(self):
        query = self.database['versions'].find({})

        results = [
            Version(**raw_version)
            async for raw_version in query
        ]

        return results
    
    async def update(self, id, entity_update):
        version = await self.get_by_id(id)
        
        await self.database['versions'] \
            .update_one(
                {'_id': version.id},
                {'$set': entity_update.model_dump(exclude_unset=True)}
            )
        
        version = await self.get_by_id(id)

        return version
    
    async def delete(self, id):
        version = await self.get_by_id(id)

        await self.database['versions'] \
            .delete_one({'_id': version.id})