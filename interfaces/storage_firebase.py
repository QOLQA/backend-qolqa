from datetime import timedelta
from fastapi import UploadFile
from firebase_admin import storage
from interfaces.storage import Storage

class FirebaseStorage(Storage):
  def uploadFile(self, basePath: str, folder: str, file: UploadFile):
    super().uploadFile(basePath, folder, file)
    blob = storage.bucket().blob(basePath + '/' + folder + '/' + file.filename)
    blob.upload_from_file(file.file)

  def getLinkDownloadable(self, basePath: str, folder: str, filename: str):
    super().getLinkDownloadable(basePath, folder, filename)
    path = basePath + '/' + folder + '/' + filename
    blob = storage.bucket().blob(path)
    url = blob.generate_signed_url(timedelta(seconds=60), method='GET')
    return { url }