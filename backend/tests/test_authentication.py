from app.core.authentication import (
    AuthenticatedPrincipal,
    AuthenticationError,
    BearerTokenAuthenticator,
)


def test_authenticated_principal_is_immutable() -> None:
    principal = AuthenticatedPrincipal(
        subject="user-1",
        role="user",
    )

    assert principal.subject == "user-1"
    assert principal.role == "user"

    try:
        principal.subject = "user-2"
    except AttributeError:
        pass
    else:
        raise AssertionError("AuthenticatedPrincipal must be immutable.")


def test_missing_authorization_is_rejected() -> None:
    authenticator = BearerTokenAuthenticator(
        credentials={
            "token": AuthenticatedPrincipal(
                subject="user-1",
                role="user",
            ),
        },
    )

    try:
        authenticator.authenticate(None)
    except AuthenticationError as exc:
        assert str(exc) == "Authentication credentials are required."
    else:
        raise AssertionError("Missing credentials must be rejected.")


def test_invalid_authorization_scheme_is_rejected() -> None:
    authenticator = BearerTokenAuthenticator(
        credentials={
            "token": AuthenticatedPrincipal(
                subject="user-1",
                role="user",
            ),
        },
    )

    for authorization in (
        "Basic token",
        "Bearer",
        "Bearer ",
        "invalid",
    ):
        try:
            authenticator.authenticate(authorization)
        except AuthenticationError as exc:
            assert str(exc) == "Invalid authentication credentials."
        else:
            raise AssertionError("Invalid credentials must be rejected.")


def test_unknown_bearer_token_is_rejected() -> None:
    authenticator = BearerTokenAuthenticator(
        credentials={
            "valid-token": AuthenticatedPrincipal(
                subject="user-1",
                role="user",
            ),
        },
    )

    try:
        authenticator.authenticate("Bearer invalid-token")
    except AuthenticationError as exc:
        assert str(exc) == "Invalid authentication credentials."
    else:
        raise AssertionError("Unknown credentials must be rejected.")


def test_valid_bearer_token_returns_principal() -> None:
    principal = AuthenticatedPrincipal(
        subject="user-1",
        role="user",
    )

    authenticator = BearerTokenAuthenticator(
        credentials={"secret-token": principal},
    )

    result = authenticator.authenticate("Bearer secret-token")

    assert result is principal


def test_bearer_scheme_is_case_insensitive() -> None:
    principal = AuthenticatedPrincipal(
        subject="user-1",
        role="user",
    )

    authenticator = BearerTokenAuthenticator(
        credentials={"secret-token": principal},
    )

    result = authenticator.authenticate("bEaReR secret-token")

    assert result is principal
