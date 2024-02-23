from fastapi import APIRouter, Request

router = APIRouter()

@router.post('')
async def create_fake_models(
    request: Request,
    num_models: int = 10,
):
    return request.app.services.seed.documents(request, num_models)




