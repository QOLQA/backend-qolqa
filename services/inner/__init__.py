from services.inner.user import user_service
from services.inner.no_sql_db import model_service
from services.seed import seed

class Services:
  def __init__(self) -> None:
    self.users = user_service
    self.models = model_service
    self.seed = seed
