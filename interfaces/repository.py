from interfaces.model import Model

class Repository:
  def create(self) -> Model:
    pass
  
  def delete(self, id: str) -> None:
    pass
  
  def get_all(self) -> list[Model]:
    pass
  
  def get_one(self, id: str) -> Model:
    pass
  
  def update(self, id: str, model: Model) -> Model:
    pass
