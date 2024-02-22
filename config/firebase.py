import os
from pathlib import Path
from dotenv import load_dotenv

from firebase_admin import credentials, firestore, initialize_app, storage
from google.cloud.firestore import Client

credentials_path = Path(__file__).parent.parent / 'serviceAccount.json'
credentials = credentials.Certificate(credentials_path)

load_dotenv()
is_local = os.environ.get('IS_LOCAL')

if is_local == 'true':
  os.environ['FIRESTORE_EMULATOR_HOST'] = 'localhost:8080'


initialize_app(credentials, {
  'storageBucket': 'developqolqa.appspot.com'
})
db: Client = firestore.client()
bucket = storage.bucket()
