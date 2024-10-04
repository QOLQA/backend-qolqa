from interfaces.repository import Repository
from interfaces.model import Model
from models.no_sql_db import NoSqlDBForm, NoSqlDB

from services.db import repo_models

class NoSqlDBService:
  def __init__(self, repo: Repository) -> None:
    self.repo = repo
    
  def create(self, modelForm: NoSqlDBForm) -> NoSqlDB:
    new_model = self.repo.create()
    model_updated = Model(id=new_model.id, data=modelForm.dict())
    model = self.repo.update(new_model.id, model_updated)
    return NoSqlDB(id=model.id, **model.data)
    
  def get_all(self) -> list[Model]:
    models = self.repo.get_all()
    models = [NoSqlDB(id=m.id, **m.data) for m in models]
    return models
  
  def get_one(self, id: str) -> NoSqlDB:
    model = self.repo.get_one(id)
    model = NoSqlDB(id=model.id, **model.data)
    return model
  
  def update(self, id: str, model_updated: NoSqlDBForm):
    collection_updated = Model(id=id, data=model_updated.dict())
    updated = self.repo.update(id, collection_updated)
    return NoSqlDB(id=updated.id, **updated.data)
    
  def delete(self, id: str) -> None:
        self.repo.delete(id)
        
model_service = NoSqlDBService(repo_models)
