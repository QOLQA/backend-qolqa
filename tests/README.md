# Tests Directory

Este directorio contiene todos los tests para el backend de QOLQA.

## Estructura de Tests

### Tests de Validación
- **test_solution_validation.py**: Tests de validación para el modelo Solution
- **test_version_validation.py**: Tests de validación para el modelo Version

### Tests de Integración
- **test_endpoints.py**: Tests de integración para los endpoints de la API

### Tests de Autenticación (Preparados para JWT)
- **test_auth.py**: Tests preparados para futura implementación de JWT

## Ejecutar Tests

### Instalar dependencias
```bash
pip install -r requirements.txt
```

### Ejecutar todos los tests
```bash
pytest
```

### Ejecutar tests específicos por categoría
```bash
# Solo tests de validación
pytest -m validation

# Solo tests de integración
pytest -m integration

# Solo tests de autenticación (actualmente skipped)
pytest -m auth
```

### Ejecutar tests de un archivo específico
```bash
pytest tests/test_solution_validation.py
pytest tests/test_version_validation.py
pytest tests/test_endpoints.py
```

### Ejecutar con cobertura
```bash
pytest --cov=. --cov-report=html
```

### Ejecutar tests con más detalle
```bash
pytest -v
pytest -vv  # Muy detallado
```

## Marcadores (Markers)

Los tests están organizados con los siguientes marcadores:

- `@pytest.mark.validation`: Tests de validación de modelos
- `@pytest.mark.integration`: Tests de integración de endpoints
- `@pytest.mark.unit`: Tests unitarios
- `@pytest.mark.auth`: Tests de autenticación (preparados para JWT)

## Fixtures Disponibles

Ver `conftest.py` para todas las fixtures disponibles:

- `client`: Cliente de prueba síncrono
- `async_client`: Cliente de prueba asíncrono
- `mock_solution_data`: Datos mock para soluciones
- `mock_version_data`: Datos mock para versiones
- `mock_user_credentials`: Credenciales mock (para JWT futuro)
- `auth_headers`: Headers de autorización (para JWT futuro)

## Tests de Autenticación JWT

Los tests en `test_auth.py` están marcados con `@pytest.mark.skip` porque la funcionalidad JWT aún no está implementada. Estos tests sirven como:

1. **Documentación** de lo que se necesitará implementar
2. **Guía** para el desarrollo futuro de autenticación
3. **Especificación** de los requisitos de seguridad

Cuando implementes JWT, simplemente remueve los decoradores `@pytest.mark.skip` y completa la lógica.

## Próximos Pasos para JWT

1. Instalar dependencias JWT:
   ```bash
   pip install python-jose[cryptography] passlib[bcrypt]
   ```

2. Crear módulos de autenticación:
   - `auth/jwt.py`: Utilidades para crear y validar tokens
   - `auth/password.py`: Hash y verificación de contraseñas
   - `auth/router.py`: Endpoints de login/register

3. Actualizar modelos:
   - Crear modelo `User` con campos: username, email, hashed_password, roles
   - Agregar campo `user_id` a Solution para ownership

4. Habilitar tests:
   - Remover `@pytest.mark.skip` de los tests en `test_auth.py`
   - Implementar la lógica real en lugar de los TODOs

## Convenciones de Testing

- Nombres de tests descriptivos en español
- Usar fixtures para datos reutilizables
- Mockear servicios externos y base de datos
- Tests independientes entre sí
- Cada test debe probar una sola cosa
