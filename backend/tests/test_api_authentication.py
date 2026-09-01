from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies.authentication import (
    get_authenticator,
    require_authenticated_principal,
)
from app.core.authentication import AuthenticatedPrincipal
from app.core.config import Settings

protected_dependency = Depends(require_authenticated_principal)


def create_test_app() -> FastAPI:
    app = FastAPI()

    @app.get("/protected")
    def protected(
        principal: AuthenticatedPrincipal = protected_dependency,
    ) -> dict[str, str]:
        return {
            "subject": principal.subject,
            "role": principal.role,
        }

    return app


def configure_test_authentication() -> None:
    settings = Settings(
        database_url="postgresql+psycopg://financial_proof:test-password@localhost:5433/financial-proof",
        api_auth_token="financial-proof-development-token",
    )

    import app.api.dependencies.authentication as authentication

    authentication.settings = settings
    get_authenticator.cache_clear()


def test_missing_credentials_return_401() -> None:
    configure_test_authentication()
    client = TestClient(create_test_app())

    response = client.get("/protected")

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required."}
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_invalid_credentials_return_401() -> None:
    configure_test_authentication()
    client = TestClient(create_test_app())

    response = client.get(
        "/protected",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required."}


def test_valid_credentials_return_authenticated_identity() -> None:
    configure_test_authentication()
    client = TestClient(create_test_app())

    response = client.get(
        "/protected",
        headers={
            "Authorization": "Bearer financial-proof-development-token",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "subject": "development-user",
        "role": "user",
    }
