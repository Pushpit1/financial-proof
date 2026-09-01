"""API authentication dependencies."""

from functools import lru_cache

from fastapi import Header, HTTPException, status

from app.core.authentication import (
    AuthenticatedPrincipal,
    AuthenticationError,
    BearerTokenAuthenticator,
)
from app.core.config import settings


@lru_cache
def get_authenticator() -> BearerTokenAuthenticator:
    """Build the API authenticator from environment configuration."""

    token = settings.api_auth_token

    if token is None or not token.get_secret_value().strip():
        return BearerTokenAuthenticator(credentials={})

    return BearerTokenAuthenticator(
        credentials={
            token.get_secret_value(): AuthenticatedPrincipal(
                subject="development-user",
                role="user",
            ),
        },
    )


def require_authenticated_principal(
    authorization: str | None = Header(default=None),
) -> AuthenticatedPrincipal:
    """Authenticate the current request and return its principal."""

    try:
        return get_authenticator().authenticate(authorization)
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
