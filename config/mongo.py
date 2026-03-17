from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from config.settings import settings

# Configurar cliente MongoDB con timeout
# socketTimeoutMS: tiempo máximo para operaciones de socket
# connectTimeoutMS: tiempo máximo para establecer conexión
# serverSelectionTimeoutMS: tiempo máximo para seleccionar servidor
motor_client = AsyncIOMotorClient(
    settings.database_url,
    socketTimeoutMS=settings.db_operation_timeout * 1000,  # Convert to milliseconds
    connectTimeoutMS=5000,  # 5 seconds for connection
    serverSelectionTimeoutMS=5000,  # 5 seconds for server selection
    maxPoolSize=50,  # Maximum connections in pool
    minPoolSize=10   # Minimum connections in pool
)

database = motor_client['qolqa']

def get_database() -> AsyncIOMotorDatabase:
    return database