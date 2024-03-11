from datetime import timedelta
from fastapi import UploadFile
from interfaces.file_storage import FileStorage

from config.firebase import bucket

class FirebaseStorage(FileStorage):
  def __init__(self, base_path: str) -> None:
    super().__init__()
    self.base_path = base_path
    self.bucket = bucket

  def upload_file(self, folder: str, file: UploadFile):
    super().upload_file(folder, file)
    blob = self.bucket.blob(self.base_path + '/' + folder + '/' )
    blob.upload_from_file(file.file)

  def get_link_downloadable(self, folder: str, filename: str, expiration: int):
    super().get_link_downloadable(folder, filename, expiration)
    blob = self.bucket.blob(self.base_path + '/' + folder + '/' + filename)
    return blob.generate_signed_url(timedelta(minutes=expiration), method='GET')
