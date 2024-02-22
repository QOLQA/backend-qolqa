from interfaces.repository import Repository
from interfaces.model import Model
from models.model import Model, ModelForm

from services.db import repo_models

class ModelService:
  def __init__(self, repo: Repository) -> None:
    self.repo = repo
    
  def create(self, modelForm: ModelForm) -> Model:
    new_model = self.repo.create()
    model_updated = Model(id=new_model.id, data=modelForm.model_dump())
    model = self.repo.update(model_updated)
    return Model(id=model.id, **model.data)
    
  def get_all(self) -> list[Model]:
    models = self.repo.get_all()
    models = [Model(id=m.id, **m.data) for m in models]
    return models
  
  def get_one(self, id: str) -> Model:
    model = self.repo.get_one(id)
    model = Model(id=model.id, **model.data)
    return model
  
  def update(self, id: str, model_updated: ModelForm):
    updated = self.repo.update(id, model_updated)
    return Model(id=updated.id, **updated.data)

model_service = ModelService(repo_models)
