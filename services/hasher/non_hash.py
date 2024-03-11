from interfaces.auth import Hasher

class BasicHasher(Hasher):
  def hash_password(self, password: str):
    super().hash_password(password)
    return password + 'hashed'

basic_hasher = BasicHasher()