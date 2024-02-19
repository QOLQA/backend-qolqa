from fastapi import APIRouter, Form, UploadFile, Request, File

router = APIRouter()

@router.post('')
async def upload_thumbnail(
  request: Request,
  thumbnail: UploadFile = File(...),
  basePath: str = Form('path'),
  folder: str = Form('folder')
):
  request.app.database.storage.uploadFile(basePath, folder, thumbnail)
  return request.app.database.storage.getLinkDownloadable(basePath, folder, thumbnail.filename)

