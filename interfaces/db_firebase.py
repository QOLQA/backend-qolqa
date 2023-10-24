from interfaces.database import Database
from firebase_admin import credentials, firestore, initialize_app

from models.Model import Model


cred = credentials.Certificate('./serviceAccount.json')

class Firebase(Database):
  def __init__(self) -> None:
    self.app = initialize_app(cred)
    self.db = firestore.client()

  def update(self, model_id: str, model: Model):
    super().update(model_id, model)
    doc_ref = self.db.collection('documents').document(model_id)
    update_data = model.model_dump(exclude_unset=True)
    doc_ref.update(update_data)
    doc = doc_ref.get()
    return doc.to_dict()
    
  def create(self, model: Model):
    super().create(model)
    ref = self.db.collection('documents').add(model.model_dump())
    # doc = ref.get()
    return model