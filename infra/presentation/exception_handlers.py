"""Global FastAPI exception handlers for domain errors.

Replaces the old ``handle_common_errors`` dispatch: domain errors propagate
uncaught from routers and dependencies, and Starlette routes each one to the
handler registered for its concrete class (MRO lookup, most specific wins).
Only the mapping lives here — domain errors keep knowing nothing about HTTP.
"""

import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from config.settings import settings
from domain.errors import (
    DomainException,
    Duplicate,
    Forbidden,
    Format,
    GoogleLoginNotConfigured,
    InvalidCredentials,
    InvalidGoogleToken,
    InvalidToken,
    Missing,
    NotFoundError,
    PasswordRequiredForLocalLogin,
)

logger = logging.getLogger(__name__)

_AUTH_HEADERS = {"WWW-Authenticate": "Bearer"}

# Concrete domain error -> (HTTP status, optional response headers).
# Deliberately keyed by concrete class: an unmapped DomainException subclass
# falls through to the Exception fallback (500), never to a wrong 4xx.
_STATUS_BY_ERROR: dict[type[DomainException], tuple[int, dict[str, str] | None]] = {
    Format: (status.HTTP_400_BAD_REQUEST, None),
    Missing: (status.HTTP_404_NOT_FOUND, None),
    NotFoundError: (status.HTTP_404_NOT_FOUND, None),
    Duplicate: (status.HTTP_409_CONFLICT, None),
    Forbidden: (status.HTTP_403_FORBIDDEN, None),
    InvalidCredentials: (status.HTTP_401_UNAUTHORIZED, _AUTH_HEADERS),
    InvalidToken: (status.HTTP_401_UNAUTHORIZED, _AUTH_HEADERS),
    PasswordRequiredForLocalLogin: (status.HTTP_403_FORBIDDEN, None),
    InvalidGoogleToken: (status.HTTP_401_UNAUTHORIZED, _AUTH_HEADERS),
    GoogleLoginNotConfigured: (status.HTTP_503_SERVICE_UNAVAILABLE, None),
}


def _domain_error_handler(status_code: int, headers: dict[str, str] | None):
    """Build an async exception handler returning ``{"detail": exc.msg}``."""

    async def handler(request: Request, exc: DomainException) -> JSONResponse:
        return JSONResponse(
            status_code=status_code,
            content={"detail": exc.msg},
            headers=headers,
        )

    return handler


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Last-resort handler for unexpected, non-domain errors.

    Logs the full stack trace for internal observability and returns a generic
    message to the client — never internal details.
    """
    logger.exception(
        "Unhandled error: %s: %s",
        type(exc).__name__,
        exc,
        extra={
            "path": request.url.path,
            "method": request.method,
            "error_type": type(exc).__name__,
        },
    )

    if settings.debug and settings.environment == "development":
        detail = f"Internal server error: {type(exc).__name__}: {exc}"
    else:
        detail = "Internal server error. Please contact support if the problem persists."

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": detail},
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register one handler per concrete domain error plus the global fallback."""
    for exc_type, (status_code, headers) in _STATUS_BY_ERROR.items():
        app.add_exception_handler(exc_type, _domain_error_handler(status_code, headers))
    app.add_exception_handler(Exception, global_exception_handler)
