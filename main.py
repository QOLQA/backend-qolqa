import contextlib
from datetime import datetime

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from solution.router import router as solutions_router
from auth.router import router as auth_router
from config.settings import settings, TypeDB

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

  app = FastAPI(lifespan=lifespan)

app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"]
)


app.include_router(auth_router, prefix='/auth', tags=['Authentication'])
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
