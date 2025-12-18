from bson import ObjectId, errors
from fastapi import HTTPException, status
import re

from utils.errors import Format

async def get_object_id(id: str | ObjectId) -> ObjectId:
    """
    Convierte y valida un ID de MongoDB de forma segura
    Previene NoSQL injection validando formato estricto
    
    Args:
        id: String o ObjectId a validar
        
    Returns:
        ObjectId validado
        
    Raises:
        HTTPException: Si el ID no es válido (400 Bad Request)
    """
    # Si ya es ObjectId, retornarlo (ya validado)
    if isinstance(id, ObjectId):
        return id
    
    # Validar que sea string
    if not isinstance(id, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID format: must be a string"
        )
    
    # Limpiar espacios en blanco
    id = id.strip()
    
    # Validar longitud (ObjectId es exactamente 24 caracteres hexadecimales)
    if len(id) != 24:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID format: must be exactly 24 characters"
        )
    
    # Validar que solo contenga caracteres hexadecimales (0-9, a-f, A-F)
    # Esto previene inyección de operadores MongoDB como $ne, $gt, etc.
    if not re.match(r'^[0-9a-fA-F]{24}$', id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID format: must contain only hexadecimal characters"
        )
    
    # Convertir a ObjectId (con validación adicional de BSON)
    try:
        return ObjectId(id)
    except (errors.InvalidId, TypeError, ValueError) as e:
        # Si aún falla, es un formato inválido
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid ObjectId format: {str(e)}"
        )


def sanitize_query_filters(filters: dict, allowed_fields: list[str]) -> dict:
    """
    Sanitiza filtros de búsqueda para prevenir NoSQL injection
    Solo permite campos específicos y tipos simples
    
    Args:
        filters: Diccionario con filtros del usuario
        allowed_fields: Lista de campos permitidos (whitelist)
        
    Returns:
        Diccionario sanitizado con solo filtros seguros
    """
    safe_filters = {}
    
    for key, value in filters.items():
        # Solo permitir campos en whitelist
        if key not in allowed_fields:
            continue
        
        # Solo permitir tipos simples (string, int, bool, None)
        # Rechazar objetos complejos (posibles operadores MongoDB)
        if isinstance(value, (str, int, bool, type(None))):
            safe_filters[key] = value
        elif isinstance(value, list):
            # Permitir listas solo si todos los elementos son tipos simples
            if all(isinstance(v, (str, int, bool, type(None))) for v in value):
                safe_filters[key] = {'$in': value}
        # Rechazar cualquier otro tipo (dict, objetos, etc.)
    
    return safe_filters
    