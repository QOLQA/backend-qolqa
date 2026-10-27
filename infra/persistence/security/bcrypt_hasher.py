"""
Bcrypt password hasher implementation (Infrastructure layer).

Implements IPasswordHasher using bcrypt.
"""
import bcrypt

from domain.security.password import IPasswordHasher


class BcryptHasher(IPasswordHasher):
    """Bcrypt implementation of IPasswordHasher."""

    def __init__(self, rounds: int = 12) -> None:
        self._rounds = rounds

    def hash(self, password: str) -> str:
        password_bytes = password.encode("utf-8")
        salt = bcrypt.gensalt(rounds=self._rounds)
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode("utf-8")

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        password_bytes = plain_password.encode("utf-8")
        hashed_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(password_bytes, hashed_bytes)