"""Authorization primitives for API requests."""

from dataclasses import dataclass
from enum import StrEnum

from app.core.authentication import AuthenticatedPrincipal


class AuthorizationError(ValueError):
    """Raised when an authenticated principal lacks permission."""


class Permission(StrEnum):
    """Actions that require explicit authorization."""

    READ_FINANCIAL_DATA = "read_financial_data"
    WRITE_FINANCIAL_DATA = "write_financial_data"
    MANAGE_CONTRACTS = "manage_contracts"
    MANAGE_GUARDIAN = "manage_guardian"
    ADMINISTER_SYSTEM = "administer_system"


@dataclass(frozen=True)
class RolePermissions:
    """Immutable permissions assigned to one role."""

    role: str
    permissions: frozenset[Permission]


ROLE_PERMISSIONS: dict[str, RolePermissions] = {
    "user": RolePermissions(
        role="user",
        permissions=frozenset(
            {
                Permission.READ_FINANCIAL_DATA,
                Permission.WRITE_FINANCIAL_DATA,
            }
        ),
    ),
    "admin": RolePermissions(
        role="admin",
        permissions=frozenset(
            {
                Permission.READ_FINANCIAL_DATA,
                Permission.WRITE_FINANCIAL_DATA,
                Permission.MANAGE_CONTRACTS,
                Permission.MANAGE_GUARDIAN,
                Permission.ADMINISTER_SYSTEM,
            }
        ),
    ),
    "system": RolePermissions(
        role="system",
        permissions=frozenset(
            {
                Permission.READ_FINANCIAL_DATA,
                Permission.WRITE_FINANCIAL_DATA,
                Permission.MANAGE_CONTRACTS,
                Permission.MANAGE_GUARDIAN,
            }
        ),
    ),
}


def authorize(
    principal: AuthenticatedPrincipal,
    permission: Permission,
) -> None:
    """Authorize a principal for one explicit permission."""

    role_permissions = ROLE_PERMISSIONS.get(principal.role)

    if role_permissions is None:
        raise AuthorizationError("Permission denied.")

    if permission not in role_permissions.permissions:
        raise AuthorizationError("Permission denied.")
