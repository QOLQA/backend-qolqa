from interfaces.repository import Repository
from services.db.firebase import FirebaseDB

repo_users: Repository = FirebaseDB('users')
repo_models: Repository = FirebaseDB('models')