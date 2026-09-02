from enum import Enum


class AuthProviderEnum(str, Enum):
    local = "local"
    google = "google"
