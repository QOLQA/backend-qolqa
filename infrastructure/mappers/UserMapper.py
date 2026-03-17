from datetime import datetime

from application.dtos.auth.AuthRequest import UserCreateRequest
from application.dtos.auth.AuthResponse import UserResponse
from domain.entities.auth.UserEntity import UserEntity


class UserMapper:
    """Stateless mapper between raw MongoDB dicts, UserEntity, and auth DTOs."""

    @staticmethod
    def to_entity(raw: dict) -> UserEntity:
        """Convert a raw MongoDB dict to a domain UserEntity."""
        return UserEntity(
            id=str(raw['_id']),
            username=raw['username'],
            email=raw['email'],
            full_name=raw.get('full_name'),
            is_active=raw.get('is_active', True),
            created_at=raw.get('created_at', datetime.utcnow()),
        )

    @staticmethod
    def from_create_request(request: UserCreateRequest, hashed_password: str) -> dict:
        """Convert a UserCreateRequest DTO + hashed_password to a MongoDB-insertable dict."""
        return {
            'username': request.username.lower(),
            'email': request.email.lower(),
            'full_name': request.full_name,
            'is_active': True,
            'hashed_password': hashed_password,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
        }

    @staticmethod
    def to_response(entity: UserEntity) -> UserResponse:
        """Convert a domain UserEntity to a UserResponse DTO."""
        return UserResponse(
            id=entity.id,
            username=entity.username,
            email=entity.email,
            full_name=entity.full_name,
            is_active=entity.is_active,
            created_at=entity.created_at,
        )
