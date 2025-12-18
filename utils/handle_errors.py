from fastapi import HTTPException, status, Request
import logging

from utils.errors import Format, Missing, Duplicate, NotFoundError
from config.settings import settings

# Logger para errores no manejados
logger = logging.getLogger(__name__)

async def handle_common_errors(exc: Exception, request: Request = None):
    """
    Maneja errores de forma segura sin exponer información sensible
    
    Args:
        exc: Excepción a manejar
        request: Request de FastAPI (opcional, para logging)
    """
    # Errores conocidos y controlados - estos son seguros de exponer
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
    
    # Para errores no esperados:
    # 1. Registrar detalles completos en logs (incluyendo stack trace)
    logger.error(
        f"Unhandled error: {type(exc).__name__}: {str(exc)}",
        exc_info=True,  # Incluye stack trace completo en logs
        extra={
            "path": request.url.path if request else "unknown",
            "method": request.method if request else "unknown",
            "error_type": type(exc).__name__,
        }
    )
    
    # 2. Retornar mensaje genérico al cliente (NO revelar detalles internos)
    if settings.debug and settings.environment == "development":
        # Solo en desarrollo con debug=True, mostrar detalles
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {type(exc).__name__}: {str(exc)}"
        )
    else:
        # En producción, mensaje genérico
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error. Please contact support if the problem persists."
        )