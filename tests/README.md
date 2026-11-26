# Tests Directory

Este directorio contiene todos los tests para el backend de QOLQA.

## Estructura de Tests

### Tests de Validación
- **test_solution_validation.py**: Tests de validación para el modelo Solution
- **test_version_validation.py**: Tests de validación para el modelo Version

### Tests de Integración
- **test_endpoints.py**: Tests de integración para los endpoints de la API
- **test_ownership_authorization.py**: Tests de ownership y autorización (admin, users, solutions, versions, queries)
- **test_rate_limiting.py**: Tests de rate limiting
- **test_google_login.py**: Tests completos de Google Login (dominio, mapper, repo, use case, DTOs, endpoint)

### Tests de Autenticación (JWT Implementado ✅)
- **test_auth.py**: Tests de JWT, bcrypt, login, registro, roles, token_version

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

# Solo tests de autenticación
pytest -m auth

# Tests de ownership/autorización
pytest tests/test_ownership_authorization.py -v

# Tests de Google Login
pytest tests/test_google_login.py -v
```

### Ejecutar tests de un archivo específico
```bash
pytest tests/test_solution_validation.py
pytest tests/test_version_validation.py
pytest tests/test_endpoints.py
pytest tests/test_auth.py
pytest tests/test_google_login.py
pytest tests/test_ownership_authorization.py
pytest tests/test_rate_limiting.py
```

### Ejecutar con cobertura
```bash
pytest --cov=. --cov-report=term-missing
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
- `@pytest.mark.auth`: Tests de autenticación JWT

## Fixtures Disponibles

Ver `conftest.py` para todas las fixtures disponibles:

- `client`: Cliente de prueba síncrono
- `async_client`: Cliente de prueba asíncrono (con DB mockeada)
- `authenticated_client`: Cliente con usuario autenticado mockeado
- `mock_solution_data`: Datos mock para soluciones
- `mock_version_data`: Datos mock para versiones
- `mock_user`: Usuario mock para autenticación
- `valid_jwt_token`: JWT token válido para testing
- `auth_headers`: Headers de autorización con JWT válido
- `mock_user_credentials`: Credenciales mock para tests de login

## Tests de Autenticación JWT

Los tests en `test_auth.py` están **habilitados y pasan** (JWT completamente implementado):
- Login exitoso y generación de token
- Credenciales inválidas (401)
- Credenciales faltantes (422)
- Acceso a endpoint protegido con token válido
- Acceso sin token (401)
- Token inválido (401)
- Expiración de token (401)
- Registro de usuario exitoso (201)
- Username duplicado (409)
- Contraseña débil (422)
- Email inválido (422)
- Hash y verificación de contraseñas bcrypt
- Creación y decodificación de JWT
- Roles de admin (200) vs usuario regular (403)
- Ownership de soluciones (403 si no es owner)

## Tests de Google Login

Los tests en `test_google_login.py` cubren:
- Errores de dominio (PasswordRequiredForLocalLogin, InvalidGoogleToken, GoogleLoginNotConfigured)
- AuthProviderEnum (local, google)
- UserEntity con campos google_id y auth_provider
- IUserRepository métodos Google (get_by_google_id, link_google_account, add_google_user)
- UserDocument campos nullable y valores Google
- UserMapper extensiones para Google
- verify_google_token (éxito, bad signature, wrong audience, expired, malformed, email_not_verified, missing sub/email)
- UserRepoImpl métodos Google (get_by_google_id, link_google_account, add_google_user con recuperación de carrera)
- DTOs GoogleLoginRequest/Response
- Caso de uso GoogleLogin (nuevo usuario, google_id existente, linking por email, colisión username, client_id no configurado)
- Guard AuthenticateUser (usuario solo Google, híbrido, inactivos)
- Exception handlers registrados para excepciones Google (403, 401, 503) en infra/presentation/exception_handlers.py
- Endpoint POST /auth/google (happy path, token inválido, client_id no configurado, usuario existente)
- Tests de integración full flow

## Convenciones de Testing

- Nombres de tests descriptivos en español
- Usar fixtures para datos reutilizables
- Mockear servicios externos y base de datos
- Tests independientes entre sí
- Cada test debe probar una sola cosa
- Estructura mirror: `tests/infra/presentation/routers/test_<router>.py` para tests de endpoints
