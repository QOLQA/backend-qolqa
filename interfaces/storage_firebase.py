from datetime import timedelta
from fastapi import UploadFile
from firebase_admin import storage
from interfaces.file_storage import FileStorage

class FirebaseStorage(FileStorage):
  def __init__(self, base_folder_name: str) -> None:
    super().__init__()
    self.base_path = base_folder_name
  
  def uploadFile(self, folder: str, file: UploadFile):
    super().uploadFile(self.base_path, folder, file)
    blob = storage.bucket().blob(self.base_path + '/' + folder + '/' + file.filename)
    blob.upload_from_file(file.file)

  def getLinkDownloadable(self, folder: str, filename: str):
    super().getLinkDownloadable(self.base_path, folder, filename)
    path = self.base_path + '/' + folder + '/' + filename
    blob = storage.bucket().blob(path)
    url = blob.generate_signed_url(timedelta(seconds=60), method='GET')
    return { url }

thumbnails_storage = FirebaseStorage('thumbnails')
