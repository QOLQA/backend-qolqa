from enum import Enum

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class TypeDB(str, Enum):
    mongo = 'mongo'
    sql = 'relational database'


class Settings(BaseSettings):
    debug: bool = False
    database_url: str
    type_db: TypeDB
    
    # JWT Security Settings
    secret_key: str = Field(
        default="dev-secret-key-CHANGE-THIS-IN-PRODUCTION-min-32-characters",
        min_length=32
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Environment
    environment: str = "development"
    
    model_config = SettingsConfigDict(env_file='.env')
    
    @property
    def is_production(self) -> bool:
        return self.environment == "production"

settings = Settings()
