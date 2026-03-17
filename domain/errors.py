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
