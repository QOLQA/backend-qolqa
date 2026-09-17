class Missing(Exception):
  def __init__(self, msg: str) -> None:
    self.msg = msg

class NotFoundError(Exception):
  def __init__(self, msg: str) -> None:
    self.msg = msg
    
class Duplicate(Exception):
  def __init__(self, msg: str) -> None:
    self.msg = msg
  
class Format(Exception):
    def __init__(self, msg: str) -> None:
      self.msg = msg

class Forbidden(Exception):
    """Raised when an authenticated user attempts an action they do not own or are not allowed to perform."""
    def __init__(self, msg: str) -> None:
        self.msg = msg


class InvalidCredentials(Exception):
    """Raised when authentication fails due to invalid username or password."""
    def __init__(self, msg: str = "Incorrect username or password") -> None:
        self.msg = msg


class InvalidToken(Exception):
    """Raised when a JWT token cannot be decoded or has been tampered with."""
    def __init__(self, msg: str = "Could not validate credentials") -> None:
        self.msg = msg


class PasswordRequiredForLocalLogin(Exception):
    """Raised when a user with auth_provider=google tries to log in via password and has no password set."""
    def __init__(self, msg: str = "This account uses Google login. Set a password or continue with Google.") -> None:
        self.msg = msg


class InvalidGoogleToken(Exception):
    """Raised when a Google ID token fails verification."""
    def __init__(self, msg: str = "Invalid Google token") -> None:
        self.msg = msg


class GoogleLoginNotConfigured(Exception):
    """Raised when GOOGLE_CLIENT_ID is not configured."""
    def __init__(self, msg: str = "Google login is not configured") -> None:
        self.msg = msg
