from interfaces.database import Database
from firebase_admin import credentials, firestore, initialize_app
from pathlib import Path
from models.Model import Model

# Obtén la ruta absoluta al archivo serviceAccount.json
service_account_path = Path(__file__).parent / "serviceAccount.json"

cred = credentials.Certificate(service_account_path)

MODELS_COLLECTION_NAME = 'models'

class Firebase(Database):
  def __init__(self) -> None:
    self.app = initialize_app(cred)
    self.db = firestore.client()

  def update(self, model_id: str, model: Model):
    super().update(model_id, model)
    doc_ref = self.db.collection(MODELS_COLLECTION_NAME).document(model_id)
    update_data = model.model_dump(exclude_unset=True)
    doc_ref.update(update_data)
    doc = doc_ref.get()
    return doc.to_dict()
    
  def create(self, model: Model):
    super().create(model)
    ref = self.db.collection(MODELS_COLLECTION_NAME).add(model.model_dump())
    # doc = ref.get()
    return model
  
  def read(self):
    models_ref = self.db.collection(MODELS_COLLECTION_NAME)
    models = [{"model_id": model.id} for model in models_ref.stream()]
    return models