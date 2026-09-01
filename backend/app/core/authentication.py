"""Authentication primitives for API requests."""

from dataclasses import dataclass


@dataclass(frozen=True)
class AuthenticatedPrincipal:
    """Immutable identity established by successful authentication."""

    subject: str
    role: str


class AuthenticationError(ValueError):
    """Raised when request authentication fails."""


class BearerTokenAuthenticator:
    """Authenticate requests using explicitly configured bearer credentials."""

    def __init__(
        self,
        credentials: dict[str, AuthenticatedPrincipal],
    ) -> None:
        self._credentials = dict(credentials)

    def authenticate(self, authorization: str | None) -> AuthenticatedPrincipal:
        """Return the principal represented by a valid Authorization header."""

        if authorization is None:
            raise AuthenticationError("Authentication credentials are required.")

        scheme, separator, token = authorization.partition(" ")

        if not separator or scheme.lower() != "bearer" or not token:
            raise AuthenticationError("Invalid authentication credentials.")

        principal = self._credentials.get(token)

        if principal is None:
            raise AuthenticationError("Invalid authentication credentials.")

        return principal
