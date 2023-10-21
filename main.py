import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import firebase_admin
from routers.documents import router as docs_router
from firebase_admin import credentials, firestore

os.environ["FIREBASE_AUTH_EMULATOR_HOST"] = "localhost:9099"
os.environ["FIRESTORE_EMULATOR_HOST"] = "localhost:8080"

# Use a service account
cred = credentials.Certificate('./serviceAccount.json')

origins = [
    "http://localhost:5173",
    "http://localhost:8080",
    "http://localhost:9099",
    "http://localhost:53288"
]

app = FastAPI()

app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"]
)

app.include_router(
    docs_router, prefix='/docs'
)


@app.on_event('startup')
def startup_db_client():
    app.firebase_app = firebase_admin.initialize_app(cred)
    # Usar este objeto para acceder a firestore
    app.db = firestore.client()


@app.get("/")
def read_root():
    return {"Hello": "World"}


if __name__ == '__main__':
    uvicorn.run(
        "main:app",
        reload=True
    )



