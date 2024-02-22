from services.inner.user import user_service
from services.inner.model import model_service

class Services:
  def __init__(self) -> None:
    self.users = user_service
    self.models = model_service
