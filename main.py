import contextlib
from datetime import datetime
import time
import logging

from fastapi import FastAPI, status, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware

from solution.router import router as solutions_router
from auth.router import router as auth_router
from api.controllers.query import router as queries_router
from config.settings import settings, TypeDB
from api.handle_errors import handle_common_errors
from utils.audit import log_rate_limit_exceeded

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Configurar rate limiter
limiter = Limiter(key_func=get_remote_address)

# Custom rate limit exception handler with audit logging
async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """
    Custom handler for rate limit exceeded errors
    Logs the event to audit log for security analysis
    """
    # Extract rate limit info from exception
    limit = getattr(exc, 'detail', 'unknown')
    
    # Try to get user info if authenticated
    user_id = None
    try:
        # Check if there's an Authorization header
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            from auth.jwt import decode_access_token
            token = auth_header.replace("Bearer ", "")
            try:
                payload = decode_access_token(token)
                user_id = payload.get("user_id")
            except:
                pass  # Token invalid or expired, remain anonymous
    except:
        pass  # No auth, remain anonymous
    
    # Log to audit system
    log_rate_limit_exceeded(
        path=request.url.path,
        method=request.method,
        limit=str(limit),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        user_id=user_id
    )
    
    # Log to application logger for immediate visibility
    logger.warning(
        f"Rate limit exceeded: {request.method} {request.url.path} "
        f"from {request.client.host if request.client else 'unknown'} "
        f"(user: {user_id or 'anonymous'})"
    )
    
    # Return standard rate limit response
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": "Rate limit exceeded. Please try again later."},
        headers={"Retry-After": "60"}  # Suggest retry after 60 seconds
    )

# Request Body Size Limit Middleware
class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to limit the size of incoming request bodies
    Prevents memory exhaustion attacks
    """
    def __init__(self, app, max_size: int = 5_000_000):
        super().__init__(app)
        self.max_size = max_size
    
    async def dispatch(self, request: Request, call_next):
        # Only check POST, PUT, PATCH requests
        if request.method in ["POST", "PUT", "PATCH"]:
            content_length = request.headers.get("content-length")
            
            if content_length:
                try:
                    content_length = int(content_length)
                    if content_length > self.max_size:
                        return JSONResponse(
                            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            content={
                                "detail": f"Request body too large. Maximum size is {self.max_size / 1_000_000:.1f} MB"
                            }
                        )
                except ValueError:
                    # Invalid content-length header
                    return JSONResponse(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        content={"detail": "Invalid Content-Length header"}
                    )
        
        response = await call_next(request)
        return response

if settings.type_db == TypeDB.sql:
  from config.sql import create_all_tables
  @contextlib.asynccontextmanager
  async def lifespan(app: FastAPI):
    await create_all_tables()
    print(settings)
    yield

  app = FastAPI(lifespan=lifespan)
else:
  @contextlib.asynccontextmanager
  async def lifespan(app: FastAPI):
    print(settings)
    yield

  app = FastAPI(
    lifespan=lifespan,
    # Configurar para usar aliases por defecto en respuestas JSON
    # Esto hace que _id se serialize como _id en lugar de id
  )

# Configurar rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, custom_rate_limit_handler)

# Agregar middleware de límite de tamaño de request
app.add_middleware(
    RequestSizeLimitMiddleware,
    max_size=settings.max_request_body_size
)

# Logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware to log all HTTP requests and responses
    Following FastAPI best practices for middleware
    """
    start_time = time.time()
    
    # Log request
    logger.info(
        f"Request: {request.method} {request.url.path} "
        f"from {request.client.host if request.client else 'unknown'}"
    )
    
    # Process request
    response = await call_next(request)
    
    # Calculate process time
    process_time = time.time() - start_time
    
    # Log response
    logger.info(
        f"Response: {request.method} {request.url.path} "
        f"Status {response.status_code} "
        f"Time {process_time:.3f}s"
    )
    
    # Add process time header
    response.headers["X-Process-Time"] = str(process_time)
    
    return response

# Security Headers Middleware - Applied to all responses
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """
    Add security headers to all responses
    Protects against common web vulnerabilities
    """
    response = await call_next(request)
    
    # Strict-Transport-Security (HSTS)
    # Forces HTTPS for 1 year, including subdomains
    if settings.is_production:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    # X-Content-Type-Options
    # Prevents MIME type sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"
    
    # X-Frame-Options
    # Prevents clickjacking attacks
    response.headers["X-Frame-Options"] = "DENY"
    
    # X-XSS-Protection
    # Legacy XSS protection (still useful for older browsers)
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    # Referrer-Policy
    # Controls how much referrer information is sent
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # Permissions-Policy (formerly Feature-Policy)
    # Restricts access to browser features
    response.headers["Permissions-Policy"] = (
        "geolocation=(), microphone=(), camera=(), payment=(), usb=(), "
        "magnetometer=(), gyroscope=(), speaker=()"
    )
    
    # Content-Security-Policy (CSP)
    # Mitigates XSS and injection attacks
    # For Swagger docs endpoints, allow cdn.jsdelivr.net resources
    # For all other endpoints, maintain strict security
    is_docs_endpoint = request.url.path in ["/docs", "/redoc", "/openapi.json"]
    
    if is_docs_endpoint:
        # Relaxed CSP for Swagger UI - allows CDN resources
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data: https:; "
            "font-src 'self' data: https://cdn.jsdelivr.net; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
    else:
        # Strict CSP for all other endpoints
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
    
    return response

# CORS Configuration - Use specific origins, not wildcards
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,  # ✅ Specific origins from config
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],  # ✅ Only necessary methods
    allow_headers=["Content-Type", "Authorization", "Accept", "Origin"],  # ✅ Only necessary headers
    max_age=3600,  # Cache preflight requests for 1 hour
)

# Exception handler global para capturar errores no manejados
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Handler global para todas las excepciones no manejadas
    Evita que se expongan stack traces al cliente
    """
    try:
        await handle_common_errors(exc, request)
    except HTTPException as http_exc:
        # Si handle_common_errors lanza HTTPException, retornarla
        return JSONResponse(
            status_code=http_exc.status_code,
            content={"detail": http_exc.detail}
        )
    except Exception as fallback_exc:
        # Último recurso: registrar y retornar error genérico
        logger.error(
            f"Critical error in exception handler: {str(fallback_exc)}",
            exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )


app.include_router(auth_router, prefix='/auth', tags=['Authentication'])
app.include_router(queries_router, prefix='/queries', tags=['Queries'])
app.include_router(solutions_router, prefix='/solutions', tags=['Solutions'])


@app.get('/health', tags=['Health'])
async def health_check():
    """
    Health check endpoint to verify service and database connectivity
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "qolqa-api",
        "environment": settings.environment,
        "database": {
            "type": settings.type_db.value,
            "status": "unknown"
        }
    }
    
    try:
        # Check database connectivity based on type
        if settings.type_db == TypeDB.sql:
            from config.sql import engine
            async with engine.connect() as conn:
                await conn.execute("SELECT 1")
                health_status["database"]["status"] = "connected"
        else:
            from config.mongo import motor_client
            # Ping MongoDB to check connection
            await motor_client.admin.command('ping')
            health_status["database"]["status"] = "connected"
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=health_status
        )
    
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["database"]["status"] = "disconnected"
        health_status["database"]["error"] = str(e)
        
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=health_status
        )
