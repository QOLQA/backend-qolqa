# Análisis de Seguridad del Backend FastAPI

## 📋 Resumen Ejecutivo

Este documento presenta un análisis exhaustivo de seguridad del backend QOLQA desarrollado con FastAPI. Se identificaron **10 vulnerabilidades críticas** y **15 mejoras recomendadas** que deben ser implementadas antes de desplegar en producción.

**Estado Actual: ⚠️ NO APTO PARA PRODUCCIÓN**

---

## 🔴 VULNERABILIDADES CRÍTICAS

### 1. **Sin Autenticación ni Autorización** (CRÍTICO)
**Severidad:** 🔴 CRÍTICA  
**CWE-ID:** CWE-306 (Missing Authentication for Critical Function)

**Problema:**
- Todos los endpoints están completamente abiertos
- Cualquier usuario puede crear, modificar o eliminar soluciones
- No hay control de acceso basado en roles (RBAC)
- No hay validación de ownership de recursos

**Impacto:**
- Pérdida total de datos
- Modificación no autorizada de información
- Imposibilidad de auditar acciones
- Violación de privacidad de usuarios

**Solución Recomendada:**
```python
# Implementar JWT con OAuth2
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta

# Configuración
SECRET_KEY = "your-secret-key-here-use-env-variable"  # ⚠️ Debe estar en .env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Crear token
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Verificar token
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    # Buscar usuario en base de datos
    return user

# Proteger endpoints
@router.post('', response_model=Solution)
async def create(
    solution_create: SolutionCreate,
    current_user: User = Depends(get_current_user),  # ✅ Requiere autenticación
    database = Depends(get_database),
):
    # Agregar user_id a la solución
    solution_create.user_id = current_user.id
    return await service.create(SolutionRepositoryNoSql(database), solution_create)
```

**Dependencias necesarias:**
```bash
pip install python-jose[cryptography] passlib[bcrypt] python-multipart
```

---

### 2. **CORS Completamente Abierto** (CRÍTICO)
**Severidad:** 🔴 CRÍTICA  
**CWE-ID:** CWE-942 (Overly Permissive Cross-domain Whitelist)

**Problema actual en `main.py`:**
```python
app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],        # ❌ Permite CUALQUIER origen
  allow_credentials=True,      # ❌ PELIGROSO con allow_origins=["*"]
  allow_methods=["*"],         # ❌ Permite todos los métodos
  allow_headers=["*"]          # ❌ Permite todos los headers
)
```

**Por qué es peligroso:**
- **Permite ataques CSRF** (Cross-Site Request Forgery)
- **Robo de tokens de autenticación** desde sitios maliciosos
- **Violación de la Same-Origin Policy**
- **allow_credentials=True con allow_origins=["*"]** es una configuración insegura

**Solución:**
```python
from fastapi.middleware.cors import CORSMiddleware
from config.settings import settings

# Definir orígenes permitidos en .env
ALLOWED_ORIGINS = [
    "http://localhost:3000",      # Frontend en desarrollo
    "http://localhost:5173",      # Vite dev server
    "https://qolqa.com",          # Producción
    "https://www.qolqa.com",      # Producción con www
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,        # ✅ Solo orígenes específicos
    allow_credentials=True,                # ✅ Seguro con orígenes específicos
    allow_methods=["GET", "POST", "PATCH", "DELETE"],  # ✅ Solo métodos necesarios
    allow_headers=["Content-Type", "Authorization"],   # ✅ Solo headers necesarios
    expose_headers=["X-Total-Count"],      # Headers expuestos al cliente
    max_age=3600,                          # Cache de preflight requests
)
```

---

### 3. **Inyección NoSQL** (CRÍTICO)
**Severidad:** 🔴 CRÍTICA  
**CWE-ID:** CWE-943 (Improper Neutralization of Special Elements in Data Query Logic)

**Problema en `repository_nosql.py`:**
```python
async def get_by_id(self, id):
    object_id = await get_object_id(id)  # ❓ ¿Valida el input?
    raw_solution = await self.database['solutions'].find_one({'_id': object_id})
```

**Vectores de ataque:**
```python
# Ataque potencial si no se valida correctamente
{
    "id": {"$ne": null}  # Retorna el primer documento
}
```

**Solución:**
```python
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException, status

async def get_object_id(id: str | ObjectId) -> ObjectId:
    """
    Convierte y valida un ID de forma segura
    """
    if isinstance(id, ObjectId):
        return id
    
    # Validar que sea un string
    if not isinstance(id, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID must be a string"
        )
    
    # Validar longitud (ObjectId es 24 caracteres hex)
    if len(id) != 24:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID format"
        )
    
    # Validar que solo contiene caracteres hexadecimales
    if not all(c in '0123456789abcdefABCDEF' for c in id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID format: must be hexadecimal"
        )
    
    try:
        return ObjectId(id)
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ObjectId format"
        )

# Nunca permitir queries arbitrarias del usuario
async def find_solutions(self, filters: dict):
    # ❌ NUNCA hacer esto:
    # results = await self.database['solutions'].find(filters)
    
    # ✅ Sanitizar y validar todos los filtros
    allowed_filters = {}
    if 'name' in filters and isinstance(filters['name'], str):
        # Escapar caracteres especiales de regex
        allowed_filters['name'] = {'$regex': f"^{re.escape(filters['name'])}"}
    
    return await self.database['solutions'].find(allowed_filters).to_list(100)
```

---

### 4. **Sin Rate Limiting** (ALTA)
**Severidad:** 🟠 ALTA  
**CWE-ID:** CWE-770 (Allocation of Resources Without Limits or Throttling)

**Problema:**
- No hay límite de requests por IP/usuario
- Vulnerable a ataques de fuerza bruta
- Vulnerable a DDoS
- Posible abuso de recursos

**Solución con SlowAPI:**
```bash
pip install slowapi
```

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Configurar limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Aplicar a endpoints sensibles
@router.post('/login')
@limiter.limit("5/minute")  # ✅ Máximo 5 intentos de login por minuto
async def login(request: Request, form: OAuth2PasswordRequestForm = Depends()):
    ...

@router.post('', response_model=Solution)
@limiter.limit("20/minute")  # ✅ Máximo 20 creaciones por minuto
async def create(request: Request, solution_create: SolutionCreate, ...):
    ...

@router.get('')
@limiter.limit("100/minute")  # ✅ Máximo 100 consultas por minuto
async def all(request: Request, ...):
    ...
```

---

### 5. **Exposición de Información Sensible en Errores** (ALTA)
**Severidad:** 🟠 ALTA  
**CWE-ID:** CWE-209 (Generation of Error Message Containing Sensitive Information)

**Problema en `handle_errors.py`:**
```python
async def handle_common_errors(exc: Exception):
    ...
    raise exc  # ❌ Expone stack traces y detalles internos
```

**Solución:**
```python
import logging
from fastapi import HTTPException, status, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

async def handle_common_errors(exc: Exception, request: Request = None):
    if isinstance(exc, Format):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.msg,
        )
    if isinstance(exc, Missing):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.msg,
        )
    if isinstance(exc, Duplicate):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=exc.msg,
        )
    
    # ✅ Registrar error completo en logs
    logger.error(
        f"Unhandled error: {type(exc).__name__}",
        exc_info=True,
        extra={
            "path": request.url.path if request else "unknown",
            "method": request.method if request else "unknown"
        }
    )
    
    # ✅ Retornar mensaje genérico al cliente
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Internal server error"  # No revelar detalles
    )

# Agregar exception handler global en main.py
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return await handle_common_errors(exc, request)
```

---

### 6. **Sin Validación de Tamaño de Input** (MEDIA)
**Severidad:** 🟡 MEDIA  
**CWE-ID:** CWE-1284 (Improper Validation of Specified Quantity in Input)

**Problema:**
- No hay límites en el tamaño de strings
- No hay límites en arrays/listas
- Posible ataque de memoria (Memory exhaustion)

**Solución:**
```python
from pydantic import BaseModel, Field, field_validator
from typing import List

class Query(BaseModel):
    id: str = Field(max_length=100)  # ✅ Límite de caracteres
    full_query: str = Field(max_length=5000)  # ✅ Límite para queries
    collections: List[str] = Field(max_length=50)  # ✅ Máximo 50 colecciones
    
    @field_validator('collections')
    @classmethod
    def validate_collections_size(cls, v: List[str]) -> List[str]:
        if len(v) > 50:
            raise ValueError('Maximum 50 collections allowed')
        for collection in v:
            if len(collection) > 100:
                raise ValueError('Collection name too long (max 100 chars)')
        return v

class SolutionBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)  # ✅ Entre 1 y 200 caracteres
    last_version_saved: str = Field(max_length=100)
    src_img: str = Field(max_length=500)  # ✅ URL limitada
    queries: List[Query] = Field(max_length=100)  # ✅ Máximo 100 queries
    
    @field_validator('src_img')
    @classmethod
    def validate_url(cls, v: str) -> str:
        # ✅ Validar que sea una URL válida
        from urllib.parse import urlparse
        try:
            result = urlparse(v)
            if not all([result.scheme, result.netloc]):
                raise ValueError('Invalid URL format')
            if result.scheme not in ['http', 'https']:
                raise ValueError('Only HTTP(S) URLs allowed')
        except Exception:
            raise ValueError('Invalid URL')
        return v

# Agregar límite global de tamaño de request
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["qolqa.com", "*.qolqa.com", "localhost"]
)

# Límite de tamaño de request body
from starlette.middleware.base import BaseHTTPMiddleware

class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_size: int = 10_000_000):  # 10 MB por defecto
        super().__init__(app)
        self.max_size = max_size
    
    async def dispatch(self, request, call_next):
        if request.method in ["POST", "PUT", "PATCH"]:
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > self.max_size:
                return JSONResponse(
                    status_code=413,
                    content={"detail": "Request entity too large"}
                )
        return await call_next(request)

app.add_middleware(RequestSizeLimitMiddleware, max_size=5_000_000)  # 5 MB
```

---

### 7. **Credenciales en Código o Sin Protección** (CRÍTICO)
**Severidad:** 🔴 CRÍTICA  
**CWE-ID:** CWE-798 (Use of Hard-coded Credentials)

**Problema:**
- Las credenciales están en `settings.py` que lee de `.env`
- ¿El archivo `.env` está en `.gitignore`? ✅ Verificar
- ¿Las credenciales de producción están seguras?

**Solución:**
```python
# config/settings.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    # Database
    database_url: str
    type_db: TypeDB
    
    # Security
    secret_key: str = Field(..., min_length=32)  # ✅ Mínimo 32 caracteres
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS
    allowed_origins: list[str] = ["http://localhost:3000"]
    
    # API Keys (para servicios externos)
    api_key_encryption_key: str = Field(..., min_length=32)
    
    # Logging
    log_level: str = "INFO"
    
    # Entorno
    environment: str = "development"  # development, staging, production
    debug: bool = False
    
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False
    )
    
    @property
    def is_production(self) -> bool:
        return self.environment == "production"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Validaciones adicionales
        if self.is_production and self.debug:
            raise ValueError("Debug mode cannot be enabled in production")

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
```

**Archivo `.env.example`:**
```bash
# Database
DATABASE_URL=mongodb://localhost:27017/qolqa
TYPE_DB=mongo

# Security (GENERAR NUEVAS CLAVES PARA PRODUCCIÓN)
SECRET_KEY=your-secret-key-minimum-32-characters-long-use-secrets-token-urlsafe
API_KEY_ENCRYPTION_KEY=another-secret-key-32-chars-min

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# Environment
ENVIRONMENT=development
DEBUG=True
LOG_LEVEL=DEBUG
```

**Generar secret keys:**
```python
import secrets
print("SECRET_KEY:", secrets.token_urlsafe(32))
print("API_KEY_ENCRYPTION_KEY:", secrets.token_urlsafe(32))
```

---

### 8. **Sin HTTPS en Producción** (CRÍTICO)
**Severidad:** 🔴 CRÍTICA  
**CWE-ID:** CWE-319 (Cleartext Transmission of Sensitive Information)

**Solución:**
```python
# main.py
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

if settings.is_production:
    # ✅ Redirigir todo el tráfico HTTP a HTTPS
    app.add_middleware(HTTPSRedirectMiddleware)
    
    # ✅ Agregar HSTS header
    from fastapi.middleware.trustedhost import TrustedHostMiddleware
    
    @app.middleware("http")
    async def add_security_headers(request, call_next):
        response = await call_next(request)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response
```

---

### 9. **Sin Logging de Auditoría** (MEDIA)
**Severidad:** 🟡 MEDIA  
**CWE-ID:** CWE-778 (Insufficient Logging)

**Problema:**
- No se registran acciones críticas (crear, modificar, eliminar)
- No se puede auditar quién hizo qué
- Dificulta investigación de incidentes

**Solución:**
```python
import logging
from datetime import datetime
import json

# Configurar logging
logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        },
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/app.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'json',
        },
        'audit': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/audit.log',
            'maxBytes': 10485760,
            'backupCount': 10,
            'formatter': 'json',
        }
    },
    'loggers': {
        '': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
        'audit': {
            'handlers': ['audit'],
            'level': 'INFO',
            'propagate': False
        }
    }
})

audit_logger = logging.getLogger('audit')

def log_audit(action: str, user_id: str, resource_type: str, resource_id: str, details: dict = None):
    """Registrar eventos de auditoría"""
    audit_logger.info(
        "Audit event",
        extra={
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "user_id": user_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "details": details or {}
        }
    )

# Usar en endpoints
@router.post('', response_model=Solution)
async def create(
    solution_create: SolutionCreate,
    current_user: User = Depends(get_current_user),
    database = Depends(get_database),
):
    solution = await service.create(SolutionRepositoryNoSql(database), solution_create)
    
    # ✅ Registrar en audit log
    log_audit(
        action="solution.create",
        user_id=current_user.id,
        resource_type="solution",
        resource_id=str(solution.id),
        details={"name": solution.name}
    )
    
    return solution
```

---

### 10. **Sin Protección contra CSRF** (MEDIA)
**Severidad:** 🟡 MEDIA  
**CWE-ID:** CWE-352 (Cross-Site Request Forgery)

**Solución con FastAPI CSRF Protect:**
```bash
pip install fastapi-csrf-protect
```

```python
from fastapi_csrf_protect import CsrfProtect
from fastapi_csrf_protect.exceptions import CsrfProtectError
from pydantic import BaseModel

class CsrfSettings(BaseModel):
    secret_key: str = settings.secret_key
    cookie_samesite: str = "lax"
    cookie_secure: bool = settings.is_production
    cookie_httponly: bool = True

@CsrfProtect.load_config
def get_csrf_config():
    return CsrfSettings()

@app.exception_handler(CsrfProtectError)
def csrf_protect_exception_handler(request: Request, exc: CsrfProtectError):
    return JSONResponse(
        status_code=403,
        content={"detail": "CSRF token validation failed"}
    )

# Proteger endpoints de modificación
@router.post('', response_model=Solution)
async def create(
    solution_create: SolutionCreate,
    csrf_protect: CsrfProtect = Depends(),
    database = Depends(get_database),
):
    csrf_protect.validate_csrf(request)  # ✅ Validar token CSRF
    ...
```

---

## 🟡 MEJORAS RECOMENDADAS

### 11. Implementar Sanitización de Inputs
```python
import bleach
from html import escape

def sanitize_string(text: str) -> str:
    """Sanitizar strings para prevenir XSS"""
    # Escapar HTML
    text = escape(text)
    # Limpiar con bleach
    text = bleach.clean(text, tags=[], strip=True)
    return text.strip()
```

### 12. Agregar Timeouts a Requests de Database
```python
# En repository_nosql.py
async def get_by_id(self, id):
    try:
        # ✅ Agregar timeout
        raw_solution = await asyncio.wait_for(
            self.database['solutions'].find_one({'_id': object_id}),
            timeout=5.0  # 5 segundos máximo
        )
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Database query timeout"
        )
```

### 13. Implementar Paginación
```python
from fastapi import Query

@router.get('', response_model=list[Solution])
async def all(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),  # ✅ Máximo 1000 items
    database = Depends(get_database),
):
    return await service.get_all(
        SolutionRepositoryNoSql(database),
        skip=skip,
        limit=limit
    )
```

### 14. Agregar Health Check Endpoint
```python
@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@app.get("/ready", tags=["Health"])
async def readiness_check(database = Depends(get_database)):
    # Verificar conexión a database
    try:
        await database.command("ping")
        return {"status": "ready"}
    except Exception:
        raise HTTPException(status_code=503, detail="Database not ready")
```

### 15. Implementar Versionado de API
```python
from fastapi import APIRouter

api_v1 = APIRouter(prefix="/api/v1")
api_v1.include_router(solutions_router, prefix='/solutions', tags=['Solutions'])

app.include_router(api_v1)
```

---

## 📊 Checklist de Seguridad Pre-Producción

- [ ] **Autenticación implementada** (JWT con OAuth2)
- [ ] **CORS correctamente configurado** (sin wildcards)
- [ ] **Rate limiting activo** (endpoints protegidos)
- [ ] **HTTPS forzado** (HTTPSRedirectMiddleware)
- [ ] **Secrets en variables de entorno** (.env no en git)
- [ ] **Logging de auditoría** (todas las acciones críticas)
- [ ] **Validación de inputs** (tamaños, tipos, formato)
- [ ] **Sanitización de outputs** (prevenir XSS)
- [ ] **Timeouts configurados** (database, external APIs)
- [ ] **Headers de seguridad** (HSTS, X-Frame-Options, etc.)
- [ ] **Dependency updates** (pip-audit, safety check)
- [ ] **Tests de seguridad** (penetration testing)
- [ ] **Documentación actualizada** (procedimientos de seguridad)
- [ ] **Backup strategy** (datos críticos)
- [ ] **Incident response plan** (qué hacer si hay breach)

---

## 🛠️ Herramientas Recomendadas

### Testing de Seguridad
```bash
# Análisis de dependencias vulnerables
pip install safety pip-audit
safety check
pip-audit

# Análisis estático de código
pip install bandit
bandit -r . -ll

# Testing de APIs
pip install pytest-security
```

### Monitoreo
```bash
# APM y error tracking
pip install sentry-sdk

# Prometheus metrics
pip install prometheus-fastapi-instrumentator
```

---

## 📚 Referencias

1. **OWASP Top 10**: https://owasp.org/www-project-top-ten/
2. **FastAPI Security**: https://fastapi.tiangolo.com/tutorial/security/
3. **CWE Database**: https://cwe.mitre.org/
4. **NIST Guidelines**: https://csrc.nist.gov/publications

---

## 👤 Revisado por

**Fecha:** 10 de Diciembre, 2025  
**Auditor:** GitHub Copilot Security Analysis  
**Versión:** 1.0

---

## ⚠️ DISCLAIMER

Este análisis identifica vulnerabilidades conocidas en el código actual. La implementación de las soluciones propuestas debe ser probada exhaustivamente antes de desplegar en producción. Se recomienda realizar una auditoría de seguridad profesional antes del lanzamiento.
