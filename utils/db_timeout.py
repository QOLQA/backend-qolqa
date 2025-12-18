"""
Database timeout utilities
Provides async timeout wrappers for database operations
"""
import asyncio
from typing import TypeVar, Callable, Any
from fastapi import HTTPException, status
import logging

from config.settings import settings

logger = logging.getLogger(__name__)

T = TypeVar('T')


async def with_timeout(
    operation: Callable[..., Any],
    *args,
    timeout: float = None,
    operation_name: str = "database operation",
    **kwargs
) -> T:
    """
    Execute a database operation with a timeout
    
    Args:
        operation: Async function to execute
        *args: Positional arguments for the operation
        timeout: Timeout in seconds (defaults to settings.db_operation_timeout)
        operation_name: Human-readable operation name for error messages
        **kwargs: Keyword arguments for the operation
        
    Returns:
        Result of the operation
        
    Raises:
        HTTPException: 504 Gateway Timeout if operation times out
        HTTPException: 500 Internal Server Error for other errors
        
    Example:
        result = await with_timeout(
            database['users'].find_one,
            {'_id': user_id},
            timeout=5.0,
            operation_name="fetch user"
        )
    """
    if timeout is None:
        timeout = settings.db_operation_timeout
    
    try:
        # Execute the operation with timeout
        result = await asyncio.wait_for(
            operation(*args, **kwargs),
            timeout=timeout
        )
        return result
        
    except asyncio.TimeoutError:
        # Log timeout for monitoring
        logger.error(
            f"Database operation timeout: {operation_name} "
            f"exceeded {timeout} seconds"
        )
        
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"Database operation timed out after {timeout} seconds. "
                   "Please try again later."
        )
        
    except Exception as e:
        # Log unexpected errors
        logger.error(
            f"Database operation error: {operation_name} failed with {type(e).__name__}: {str(e)}",
            exc_info=True
        )
        
        # Re-raise if it's already an HTTPException
        if isinstance(e, HTTPException):
            raise
        
        # Otherwise, wrap in generic error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while accessing the database"
        )


class TimeoutError(Exception):
    """Custom exception for database timeout errors"""
    pass
