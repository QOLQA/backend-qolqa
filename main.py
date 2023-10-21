import os

import uvicorn
from fastapi import FastAPI
from typing import Union
from fastapi.middleware.cors import CORSMiddleware
import firebase_admin
from firebase_admin import credentials, firestore

from routers.documents import router as dogs_router

os.environ["FIREBASE_AUTH_EMULATOR_HOST"] = "localhost:9099"
os.environ["FIRESTORE_EMULATOR_HOST"] = "localhost:8080"

# Use a service account
cred = credentials.Certificate('./serviceAccount.json')

origins = [
  "http://localhost:5173"
]

app = FastAPI()

app.add_middleware(
  CORSMiddleware,
  allow_origins=origins,
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"]
)


@app.on_event('startup')
def startup_db_client():
    app.firebase_app = firebase_admin.initialize_app(cred)
    # Usar este objeto para acceder a la firestore
    app.db = firestore.client()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}


@app.get("/models/{modelId}")
def update_model():

    return {"message": "Update correcto"}


if __name__ == '__main__':
    uvicorn.run(
        "main:app",
        reload=True
    )



