from interfaces.repository import Repository
from interfaces.model import Model
from models.user import User, UserForm
from interfaces.auth import Hasher

from services.db import repo_users
from services.hasher import hasher

class UserService:
  def __init__(self, repo: Repository, hasher: Hasher) -> None:
    self.repo = repo
    self.hasher = hasher
    
  def create(self, userForm: UserForm) -> User:
    new_model = self.repo.create()
    userForm.password = self.hasher.hash_password(userForm.password)
    model_updated = Model(id=new_model.id, data=userForm.model_dump())
    user = self.repo.update(id=new_model.id, model=model_updated)
    return User(id=user.id, **user.data)
    
  def get_all(self) -> list[User]:
    models = self.repo.get_all()
    users = [User(id=m.id, **m.data) for m in models]
    return users
  
  def get_one(self, id: str):
    model = self.repo.get_one(id)
    user = User(id=model.id, **model.data)
    return user
  
  def get_by_username(self, username: str) -> User:
    users = self.get_all()
    return [
      user
      for user in users
      if user.username == username
    ][0]
    
  def update(self, id: str, user: UserForm):
    user_updated = Model(id=id, data=user.model_dump())
    return self.repo.update(id, user_updated)

user_service = UserService(repo_users, hasher=hasher)
