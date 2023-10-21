
from fastapi import APIRouter, Request, Body
from models import Document

router = APIRouter()


@router.patch('/documents/{document_id}')
def update_document(
		document_id: str,
		request: Request,
		document: Document = Body(...)
):
	# Acceder a la instancia de firestore en la aplicación
	doc_ref = request.app.db.collection('documents').document(document_id)
	update_data = document.model_dump(exclude_unset=True)
	doc_ref.update(update_data)
	# recuperar los datos actualizados
	doc = doc_ref.get()
	# retornar el objeto json
	return doc.to_dict()


