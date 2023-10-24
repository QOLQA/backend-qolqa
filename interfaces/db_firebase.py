from interfaces.database import Database
from firebase_admin import credentials, firestore, initialize_app

from models.Document import Document


cred = credentials.Certificate('./serviceAccount.json')

class Firebase(Database):
  def __init__(self) -> None:
    self.app = initialize_app(cred)
    self.db = firestore.client()

  def update(self, document_id: str, document: Document):
    super().update(document_id, document)
    doc_ref = self.db.collection('documents').document(document_id)
    update_data = document.model_dump(exclude_unset=True)
    doc_ref.update(update_data)
    doc = doc_ref.get()
    return doc.to_dict()
    
  def create(self, document: Document):
    super().create(document)
    ref = self.db.collection('documents').add(document.model_dump())
    # doc = ref.get()
    return document