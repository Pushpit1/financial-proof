"""API authorization dependencies."""

from fastapi import Depends, HTTPException, status

from app.api.dependencies.authentication import (
    require_authenticated_principal,
)
from app.core.authentication import AuthenticatedPrincipal
from app.core.authorization import (
    AuthorizationError,
    Permission,
    authorize,
)

_authenticated_principal_dependency = Depends(
    require_authenticated_principal,
)


class PermissionDependency:
    """FastAPI dependency enforcing one explicit permission."""

    def __init__(self, permission: Permission) -> None:
        self.permission = permission

    def __call__(
        self,
        principal: AuthenticatedPrincipal = _authenticated_principal_dependency,
    ) -> AuthenticatedPrincipal:
        try:
            authorize(principal, self.permission)
        except AuthorizationError as exc:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied.",
            ) from exc

        return principal


def require_permission(permission: Permission) -> PermissionDependency:
    """Create a stable dependency requiring one permission."""

    return PermissionDependency(permission)
