import uvicorn

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.models import router as models_router
from routers.fake import router as fake_router
from routers.thumbnails import router as thumbnails_router
from routers.user import router as users_router
from interfaces.db_firebase import Firebase
from services.inner import Services

app = FastAPI()

app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"]
)

app.include_router(
    models_router, prefix='/models'
)

app.include_router(
    fake_router, prefix='/fake'
)

app.include_router(
    thumbnails_router, prefix='/thumbnails'
)

app.include_router(users_router, prefix='/users')

@app.on_event('startup')
def startup_db_client():
    app.database = Firebase()
    app.services = Services()


@app.get("/")
def read_root():
    return {"Hello": "World"}


if __name__ == '__main__':
    uvicorn.run(
        "main:app",
        reload=True
    )



