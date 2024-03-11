from interfaces.file_storage import FileStorage
from services.file_storage.firebase import FirebaseStorage

thumbnails_storage: FileStorage = FirebaseStorage('thumbnails')
