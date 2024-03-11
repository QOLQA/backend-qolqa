from interfaces.auth import Hasher
from services.hasher.non_hash import basic_hasher

hasher: Hasher = basic_hasher
