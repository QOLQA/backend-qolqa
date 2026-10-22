from enum import Enum

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr, field_validator, ValidationError

# Default development secret key — MUST be replaced before running in production.
DEFAULT_DEV_SECRET_KEY = "dev-secret-key-CHANGE-THIS-IN-PRODUCTION-min-32-characters"

# Known unsafe secret keys. Rejected when environment == "production".
UNSAFE_SECRET_KEYS = [
    DEFAULT_DEV_SECRET_KEY,
    "change-this-secret-key",
    "secret",
    "secret-key",
]


class TypeDB(str, Enum):
    mongo = 'mongo'
    sql = 'relational database'


class Settings(BaseSettings):
    debug: bool = False
    database_url: str
    type_db: TypeDB

    # Environment
    # NOTE: declared BEFORE secret_key on purpose — a field_validator can only
    # read already-validated fields from `info.data`, so `environment` must be
    # declared first for the production guard below to ever fire.
    environment: str = "development"

    # JWT Security Settings
    # SecretStr masks the value in repr()/str() so it cannot leak into logs.
    # validate_default=True makes the production guard fire even when the
    # value comes from the default instead of an explicit argument.
    secret_key: SecretStr = Field(
        default=DEFAULT_DEV_SECRET_KEY,
        min_length=32,
        validate_default=True,
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 300

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

    # Google OAuth
    google_client_id: str | None = None
    
    # Request body size limit (in bytes)
    max_request_body_size: int = Field(
        default=5_000_000,  # 5 MB
        description="Maximum request body size in bytes (default 5MB)"
    )
    
    model_config = SettingsConfigDict(env_file='.env')
    
    @property
    def is_production(self) -> bool:
        return self.environment == "production"
    
    @field_validator('secret_key', mode='before')
    @classmethod
    def validate_secret_key_in_production(cls, v, info) -> str:
        """
        Validate the raw secret key BEFORE Pydantic coerces it to SecretStr.

        Rules:
        - The key must be a string of at least 32 characters (always enforced).
        - In production, known default/weak keys are rejected.

        The validator runs in `mode='before'` because `SecretStr` does not
        expose its inner value to the normal constraint machinery, so the raw
        `str` is inspected here and returned untouched for Pydantic to coerce.
        """
        if isinstance(v, SecretStr):
            v = v.get_secret_value()

        if not isinstance(v, str):
            raise ValueError(
                "🔒 SECURITY ERROR: secret_key must be a string."
            )

        if len(v) < 32:
            raise ValueError(
                "🔒 SECURITY ERROR: secret_key must be at least 32 characters long."
            )

        # Get environment from the data being validated.
        # `environment` is declared before `secret_key`, so it is present here.
        environment = info.data.get('environment', 'development')

        # In production, reject default or weak keys
        if environment == "production" and v.lower() in [k.lower() for k in UNSAFE_SECRET_KEYS]:
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
