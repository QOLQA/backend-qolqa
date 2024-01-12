import os
import uvicorn
from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.models import router as models_router
from routers.fake import router as fake_router
from interfaces.db_firebase import Firebase
from interfaces.database import Database

load_dotenv()

is_local = os.environ.get("IS_LOCAL")

print('is local', is_local)

if is_local == 'true':
    os.environ["FIREBASE_AUTH_EMULATOR_HOST"] = "localhost:9099"
    os.environ["FIRESTORE_EMULATOR_HOST"] = "localhost:8080"

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

@app.on_event('startup')
def startup_db_client():
    app.database: Database = Firebase()


@app.get("/")
def read_root():
    return {"Hello": "World"}


if __name__ == '__main__':
    uvicorn.run(
        "main:app",
        reload=True
    )



