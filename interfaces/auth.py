class Hasher:
  def hash_password(self, plain_password: str):
    pass
  
  def verify_password(self, plain_password: str, hashed_password):
    pass

class Auth:
  def __init__(self, hasher: Hasher) -> None:
    self.hasher = hasher

  def create_user(self):
    pass

  def decode_token(self, token: str):
    pass

  def hash_password(self, password: str):
    pass

  def get_user(self, id: str):
    pass
  