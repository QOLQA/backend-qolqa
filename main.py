from fastapi import FastAPI
from typing import Union
from fastapi.middleware.cors import CORSMiddleware
import firebase_admin
from firebase_admin import credentials, firestore

# Use a service account
cred = credentials.Certificate('./serviceAccount.json')

app = firebase_admin.initialize_app(cred)

# Usar este objeto para acceder a la firestore
db = firestore.client()

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

@app.get("/")
def read_root():
  return {"Hello": "World"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
  return {"item_id": item_id, "q": q}



