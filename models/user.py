from pydantic import BaseModel

class User(BaseModel):
  id: str
  username: str
  password: str

class UserForm(BaseModel):
  username: str
  password: str
