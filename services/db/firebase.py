from interfaces.model import Model
from interfaces.repository import Repository
from config.firebase import db

from fastapi import HTTPException, status

class FirebaseDB(Repository):
  def __init__(self, collection_name: str) -> None:
    super().__init__()
    self.collection_name = collection_name
    self.db = db

  def create(self) -> Model:
    super().create()
    doc_ref = self.db.collection(self.collection_name).document()
    return Model(doc_ref.id, {})
    
  def delete(self, model: Model) -> None:
    super().delete(model)
    doc_ref = self.db.collection(self.collection_name).document(model.id)
    doc = doc_ref.get()
    if doc.exists:
      doc_ref.delete()
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail=f'Not exist document with {id} id in {self.collection_name} collection'
    )
    
  def get_all(self) -> list[Model]:
    super().get_all()
    docs = self.db.collection(self.collection_name).stream()
    return [
      Model(id=doc.id, data=doc.to_dict())
      for doc in docs
    ]
    
  def get_one(self, id: str) -> Model:
    super().get_one(id)
    doc_ref = self.db.collection(self.collection_name).document(id)
    doc = doc_ref.get()
    if doc.exists:
      return Model(id, doc.to_dict())
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail=f'Not exist document with {id} id in {self.collection_name} collection'
    )
    
  def update(self, id: str, model: Model) -> Model:
    super().update(id, model)
    model_ref = self.db.collection(self.collection_name).document(id)
    model_ref.set(model.data)
    model = model_ref.get()
    return Model(model.id, model.to_dict())
    # doc_ref = self.db.collection(self.collection_name).document(id)
    # doc = doc_ref.get()
    # if doc.exists:
    #   doc_ref.update(model)
    #   doc = doc_ref.get()
    #   return Model(id, doc.to_dict())
    # raise HTTPException(
    #   status_code=status.HTTP_404_NOT_FOUND,
    #   detail=f'Not exist document with {id} id in {self.collection_name} collection'
    # )
