
from fastapi import APIRouter, Request, Body
from models.Model import Model

router = APIRouter()


@router.patch('/{model_id}')
def update_document(
  model_id: str,
  request: Request,
  model: Model = Body(...)
):
	return request.app.database.update(model_id, model)

@router.post('')
def create_document(
  request: Request,
  model: Model = Body(...)
):
  return request.app.database.create(model)


