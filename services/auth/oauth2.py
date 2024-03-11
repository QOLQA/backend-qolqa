from fastapi import Security, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from interfaces.auth import Auth, Hasher
from interfaces.repository import Repository
from models.user import User
from services.db import repo_users
from services.hasher import hasher

class Oauth2(Auth):
  security = HTTPBearer()
  
  def __init__(self, hasher: Hasher, repo_users: Repository) -> None:
    super().__init__(hasher)
    self.repo_users = repo_users
  
  def hash_password(self, password: str):
    super().hash_password(password)
    return self.hasher.hash_password(password)
  
  def get_user(self, auth: HTTPAuthorizationCredentials = Security(security)) -> User | None:
    id = auth.credentials
    users = self._get_users()
    if id in users:
      return users[id]
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail='User does not exist'
    )
  
  def _get_users(self) -> dict[str, User]:
    models = self.repo_users.get_all()
    users = {
      m.id: User(id=m.id, **m.data)
      for m in models
    }
    return users
  
oauth2 = Oauth2(hasher, repo_users)
