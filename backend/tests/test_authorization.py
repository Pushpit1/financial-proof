from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

import app.api.dependencies.authentication as authentication
from app.api.dependencies.authorization import require_permission
from app.core.authentication import AuthenticatedPrincipal
from app.core.authorization import Permission
from app.core.config import Settings


def configure_test_authentication() -> None:
    authentication.settings = Settings(
        database_url=(
            "postgresql+psycopg://financial_proof:"
            "test-password@localhost:5433/financial_proof"
        ),
        api_auth_token="financial-proof-development-token",
    )
    authentication.get_authenticator.cache_clear()


def test_user_can_read_financial_data() -> None:
    principal = AuthenticatedPrincipal(
        subject="user-1",
        role="user",
    )

    dependency = require_permission(Permission.READ_FINANCIAL_DATA)

    assert dependency(principal) == principal


def test_user_can_write_financial_data() -> None:
    principal = AuthenticatedPrincipal(
        subject="user-1",
        role="user",
    )

    dependency = require_permission(Permission.WRITE_FINANCIAL_DATA)

    assert dependency(principal) == principal


def test_user_cannot_manage_contracts() -> None:
    principal = AuthenticatedPrincipal(
        subject="user-1",
        role="user",
    )

    dependency = require_permission(Permission.MANAGE_CONTRACTS)

    try:
        dependency(principal)
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 403
        assert getattr(exc, "detail", None) == "Permission denied."
    else:
        raise AssertionError("Expected permission denial.")


def test_unknown_role_is_denied() -> None:
    principal = AuthenticatedPrincipal(
        subject="unknown",
        role="unknown",
    )

    dependency = require_permission(Permission.READ_FINANCIAL_DATA)

    try:
        dependency(principal)
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 403
        assert getattr(exc, "detail", None) == "Permission denied."
    else:
        raise AssertionError("Expected permission denial.")


def test_admin_can_manage_contracts() -> None:
    principal = AuthenticatedPrincipal(
        subject="admin-1",
        role="admin",
    )

    dependency = require_permission(Permission.MANAGE_CONTRACTS)

    assert dependency(principal) == principal


def test_system_cannot_administer_system() -> None:
    principal = AuthenticatedPrincipal(
        subject="system-1",
        role="system",
    )

    dependency = require_permission(Permission.ADMINISTER_SYSTEM)

    try:
        dependency(principal)
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 403
        assert getattr(exc, "detail", None) == "Permission denied."
    else:
        raise AssertionError("Expected permission denial.")


def test_api_permission_dependency_denies_user() -> None:
    configure_test_authentication()

    app = FastAPI()

    @app.get(
        "/protected",
        dependencies=[Depends(require_permission(Permission.MANAGE_CONTRACTS))],
    )
    def protected() -> dict[str, str]:
        return {"status": "ok"}

    client = TestClient(app)

    response = client.get(
        "/protected",
        headers={
            "Authorization": "Bearer financial-proof-development-token",
        },
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Permission denied."}


def test_api_permission_dependency_allows_admin() -> None:
    configure_test_authentication()

    app = FastAPI()

    @app.get(
        "/protected",
        dependencies=[Depends(require_permission(Permission.MANAGE_CONTRACTS))],
    )
    def protected() -> dict[str, str]:
        return {"status": "ok"}

    # Override authentication so this test exercises authorization
    # with an administrator principal.
    app.dependency_overrides[
        authentication.require_authenticated_principal
    ] = lambda: AuthenticatedPrincipal(
        subject="admin-1",
        role="admin",
    )

    client = TestClient(app)

    response = client.get(
        "/protected",
        headers={
            "Authorization": "Bearer financial-proof-development-token",
        },
    )

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
