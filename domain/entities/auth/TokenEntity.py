from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class TokenEntity:
    """Pure domain entity for an authentication token."""

    access_token: str
    token_type: str = "bearer"
    expires_at: datetime | None = None

    # ------------------------------------------------------------------ #
    # Factory Methods
    # ------------------------------------------------------------------ #

    @classmethod
    def create(cls, access_token: str, expires_in_minutes: int = 30) -> "TokenEntity":
        """Create a new token with expiration."""
        if not access_token:
            raise ValueError("Access token cannot be empty")
        return cls(
            access_token=access_token,
            token_type="bearer",
            expires_at=datetime.utcnow() + timedelta(minutes=expires_in_minutes),
        )

    # ------------------------------------------------------------------ #
    # Business Methods
    # ------------------------------------------------------------------ #

    def is_expired(self) -> bool:
        """Check if token is expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() >= self.expires_at

    def time_until_expiry(self) -> timedelta | None:
        """Return time remaining until expiry, or None if no expiry set."""
        if self.expires_at is None:
            return None
        remaining = self.expires_at - datetime.utcnow()
        return remaining if remaining.total_seconds() > 0 else timedelta(0)

    def refresh(self, new_access_token: str, expires_in_minutes: int = 30) -> None:
        """Refresh the token with a new access token."""
        if not new_access_token:
            raise ValueError("Access token cannot be empty")
        self.access_token = new_access_token
        self.expires_at = datetime.utcnow() + timedelta(minutes=expires_in_minutes)