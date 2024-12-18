import contextlib

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from solution.router import router as solutions_router
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


app.include_router(solutions_router, prefix='/solutions', tags=['Solutions'])
