from fastapi import HTTPException, status, Request
import logging

from domain.errors import Format, Missing, Duplicate, NotFoundError, Forbidden, InvalidCredentials
from config.settings import settings

# Logger for unhandled errors
logger = logging.getLogger(__name__)

async def handle_common_errors(exc: Exception, request: Request | None = None) -> None:
    """
    Safely handle exceptions without exposing sensitive internal details.

    Args:
        exc: Exception to handle
        request: FastAPI Request (optional, used for logging context)
    """
    # Known, controlled domain errors — safe to expose to the client
    if isinstance(exc, Format):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.msg,
        )
    if isinstance(exc, (Missing, NotFoundError)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.msg,
        )
    if isinstance(exc, Duplicate):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=exc.msg,
        )
    if isinstance(exc, Forbidden):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=exc.msg,
        )
    if isinstance(exc, InvalidCredentials):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=exc.msg,
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Unexpected errors:
    # 1. Log full details including stack trace for internal observability
    logger.error(
        f"Unhandled error: {type(exc).__name__}: {str(exc)}",
        exc_info=True,  # Includes full stack trace in logs
        extra={
            "path": request.url.path if request else "unknown",
            "method": request.method if request else "unknown",
            "error_type": type(exc).__name__,
        }
    )

    # 2. Return a generic message to the client — never expose internal details
    if settings.debug and settings.environment == "development":
        # In development with debug=True, show error details
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {type(exc).__name__}: {str(exc)}"
        )
    else:
        # In production, return a generic message
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error. Please contact support if the problem persists."
        )
