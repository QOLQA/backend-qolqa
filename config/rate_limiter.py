"""
Shared rate limiter instance.
Single instance used across all controllers to ensure consistent rate limiting
even with multiple workers (when using shared storage like Redis).
"""
from slowapi import Limiter
from slowapi.util import get_remote_address


# Single shared limiter instance
limiter = Limiter(key_func=get_remote_address)

__all__ = ["limiter"]