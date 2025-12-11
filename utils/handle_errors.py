from fastapi import HTTPException, status

from utils.errors import Format, Missing, Duplicate, NotFoundError

async def handle_common_errors(exc: Exception):
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
    raise exc # Maneja otros errores