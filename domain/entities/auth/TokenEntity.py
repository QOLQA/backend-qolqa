from pydantic import BaseModel


class TokenEntity(BaseModel):
    """Pure domain entity for an authentication token."""

    access_token: str
    token_type: str = "bearer"
