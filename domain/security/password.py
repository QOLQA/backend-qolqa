"""
Password hashing port (Domain layer).

Defines the contract for password hashing and verification.
Implementations live in infrastructure/security/.
"""
from abc import ABC, abstractmethod


class IPasswordHasher(ABC):
    """Abstract password hasher interface."""

    @abstractmethod
    def hash(self, password: str) -> str:
        """Hash a plain text password."""
        ...

    @abstractmethod
    def verify(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a plain password against a hash."""
        ...