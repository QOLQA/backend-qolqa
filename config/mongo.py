from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from config.settings import settings

# motor_client = AsyncIOMotorClient('mongodb://localhost:27019')
motor_client = AsyncIOMotorClient(settings.database_url)
database = motor_client['qolqa']

def get_database() -> AsyncIOMotorDatabase:
    return database