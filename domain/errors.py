class Missing(Exception):
  def __init__(self, msg: str) -> None:
    self.msg = msg

class NotFoundError(Exception):
  def __init__(self, msg: str) -> None:
    self.msg = msg
    
class Duplicate(Exception):
  def __init__(self, msg: str) -> None:
    self.msg = msg
  
class Format(Exception):
    def __init__(self, msg: str) -> None:
      self.msg = msg

class Forbidden(Exception):
    """Raised when an authenticated user attempts an action they do not own or are not allowed to perform."""
    def __init__(self, msg: str) -> None:
        self.msg = msg


class InvalidCredentials(Exception):
    """Raised when authentication fails due to invalid username or password."""
    def __init__(self, msg: str = "Incorrect username or password") -> None:
        self.msg = msg


class InvalidToken(Exception):
    """Raised when a JWT token cannot be decoded or has been tampered with."""
    def __init__(self, msg: str = "Could not validate credentials") -> None:
        self.msg = msg
