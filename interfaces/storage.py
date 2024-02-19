from fastapi import UploadFile

class Storage:
  def uploadFile(self, basePath: str, folder: str, file: UploadFile):
    pass
  
  def getLinkDownloadable(self, basePath: str, folder: str, filename: str):
    pass

