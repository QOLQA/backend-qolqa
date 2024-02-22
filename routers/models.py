
from fastapi import APIRouter, Request, Body
from models.model import Model, ModelForm
from utils.graph import crear_grafo

router = APIRouter()


@router.patch('/{model_id}')
def update_document(
  model_id: str,
  request: Request,
  model: ModelForm = Body(...)
):
	return request.app.services.models.update(model_id, model)

@router.post('')
def create_document(
  request: Request,
  model: Model = Body(...)
):
  return request.app.services.models.create(model)


@router.get('')
def get_all_models(
  request: Request
):
  return request.app.services.models.get_all()


@router.get('/{model_id}')
def get_single_model(
  model_id: str, 
  request: Request
):
  return request.app.services.models.get_one(model_id)



@router.get('/graph/{model_id}')
def get_single_graph(
  model_id: str,
  request: Request
):
  model: Model = request.app.services.models.get_one(model_id)
  return crear_grafo(model.model_dump())



