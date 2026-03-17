from enum import Enum

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator, ValidationError

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
    access_token_expire_minutes: int = 300
    
    # Environment
    environment: str = "development"
    
    # CORS Settings
    # Using str type with validator to avoid JSON parsing issues
    allowed_origins: str | list[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"]
    )
    
    # Database timeout settings (in seconds)
    db_operation_timeout: int = Field(
        default=10,
        description="Timeout for database operations in seconds"
    )
    
    # Request body size limit (in bytes)
    max_request_body_size: int = Field(
        default=5_000_000,  # 5 MB
        description="Maximum request body size in bytes (default 5MB)"
    )
    
    model_config = SettingsConfigDict(env_file='.env')
    
    @property
    def is_production(self) -> bool:
        return self.environment == "production"
    
    @field_validator('secret_key')
    @classmethod
    def validate_secret_key_in_production(cls, v: str, info) -> str:
        """
        Validate that secret_key is not the default value in production
        This prevents a critical security vulnerability
        """
        # Get environment from the data being validated
        environment = info.data.get('environment', 'development')
        
        # List of unsafe default values
        unsafe_defaults = [
            "dev-secret-key-CHANGE-THIS-IN-PRODUCTION-min-32-characters",
            "change-this-secret-key",
            "secret",
            "secret-key",
        ]
        
        # In production, reject default or weak keys
        if environment == "production" and v.lower() in [k.lower() for k in unsafe_defaults]:
            raise ValueError(
                "🔒 SECURITY ERROR: Cannot use default secret_key in production! "
                "Please set a secure SECRET_KEY in your .env file. "
                "Generate one with: openssl rand -hex 32"
            )
        
        return v
    
    @field_validator('allowed_origins', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        """
        Parse ALLOWED_ORIGINS from comma-separated string or list
        Handles both formats:
        - Comma-separated string: "http://localhost:3000,http://localhost:5173"
        - JSON array: ["http://localhost:3000", "http://localhost:5173"]
        """
        if isinstance(v, str):
            # If it's already a JSON-like string, it will be handled by Pydantic
            # Otherwise, split by comma
            v = v.strip()
            if not v:
                return []
            # Try to handle comma-separated values
            if ',' in v and not v.startswith('['):
                return [origin.strip() for origin in v.split(',') if origin.strip()]
            # Single origin or will be handled by Pydantic's JSON parser
            return [origin.strip() for origin in v.split(',') if origin.strip()]
        return v

settings = Settings()
