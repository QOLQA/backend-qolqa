from fastapi import UploadFile

class FileStorage:
  def upload_file(self, folder: str, file: UploadFile):
    pass
  
  def get_link_downloadable(self, folder: str, filename: str, expiration: int):
    pass

