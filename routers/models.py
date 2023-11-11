
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


@router.get('/')
def get_all_models(
  request: Request
):
  models = request.app.database.read()
  return models


@router.get('/{model_id}')
def get_single_model(
  model_id: str, 
  request: Request
):
  model_ref = request.app.database.db.collection('models').document(model_id)
  model = model_ref.get()

  if model.exists:
    return model.to_dict()
  return {"error": "Model not found"}

