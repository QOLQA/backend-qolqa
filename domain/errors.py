"""Domain errors.

Every error the business layer can raise derives from ``DomainException`` so
the presentation layer can map them to HTTP responses without catching a
blind ``Exception``. Authentication failures are further grouped under
``AuthException``.
"""


class DomainException(Exception):
    """Base class for every domain error."""

    def __init__(self, msg: str) -> None:
        self.msg = msg


class Missing(DomainException):
    def __init__(self, msg: str) -> None:
        self.msg = msg


class NotFoundError(DomainException):
    def __init__(self, msg: str) -> None:
        self.msg = msg


class Duplicate(DomainException):
    def __init__(self, msg: str) -> None:
        self.msg = msg


class Format(DomainException):
    def __init__(self, msg: str) -> None:
        self.msg = msg


class Forbidden(DomainException):
    """Raised when an authenticated user attempts an action they do not own or are not allowed to perform."""

    def __init__(self, msg: str) -> None:
        self.msg = msg


class AuthException(DomainException):
    """Base class for authentication failures (bad credentials, invalid tokens, wrong provider)."""


class InvalidCredentials(AuthException):
    """Raised when authentication fails due to invalid username or password."""

    def __init__(self, msg: str = "Incorrect username or password") -> None:
        self.msg = msg


class InvalidToken(AuthException):
    """Raised when a JWT token cannot be decoded or has been tampered with."""

    def __init__(self, msg: str = "Could not validate credentials") -> None:
        self.msg = msg


class PasswordRequiredForLocalLogin(AuthException):
    """Raised when a user with auth_provider=google tries to log in via password and has no password set."""

    def __init__(self, msg: str = "This account uses Google login. Set a password or continue with Google.") -> None:
        self.msg = msg


class InvalidGoogleToken(AuthException):
    """Raised when a Google ID token fails verification."""

    def __init__(self, msg: str = "Invalid Google token") -> None:
        self.msg = msg


class GoogleLoginNotConfigured(DomainException):
    """Raised when GOOGLE_CLIENT_ID is not configured."""

    def __init__(self, msg: str = "Google login is not configured") -> None:
        self.msg = msg
