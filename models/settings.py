from enum import Enum

from pydantic_settings import BaseSettings, SettingsConfigDict

class TypeDB(str, Enum):
    mongo = 'mongo'
    sql = 'relational database'


class Settings(BaseSettings):
    debug: bool = False
    database_url: str
    type_db: TypeDB
    
    model_config = SettingsConfigDict(env_file='.env')

settings = Settings()
