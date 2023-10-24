
from fastapi import APIRouter, Request, Body
from models.Document import Document

router = APIRouter()


@router.patch('/{document_id}')
def update_document(
  document_id: str,
  request: Request,
  document: Document = Body(...)
):
	return request.app.database.update(document_id, document)

@router.post('')
def create_document(
  request: Request,
  document: Document = Body(...)
):
  return request.app.database.create(document)


