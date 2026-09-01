# Financial Proof Security Threat Model

## 1. Purpose

This document defines the security boundaries and primary threats for the
Financial Proof backend.

The system processes financial claims, evidence, contracts, payment-provider
webhooks, financial actions, Guardian decisions, and AI investigation requests.

The security objective is:

> No untrusted input, unauthorized identity, AI tool, webhook, or application
> caller may cause a sensitive financial action without passing the required
> validation, authorization, replay protection, and Financial Guardian checks.

---

## 2. Assets

The primary protected assets are:

- Financial contract definitions.
- Financial claims and evidence.
- Financial proof results.
- Payment-provider credentials.
- API authentication credentials.
- Webhook signatures and raw webhook payloads.
- Payment capture and refund operations.
- Guardian decisions and audit records.
- AI investigation tool access.
- Correlation and audit information.
- Application configuration and database credentials.

---

## 3. Trust Boundaries

### Boundary A — External API -> Authentication

Untrusted clients enter through API endpoints.

Required controls:

- Bearer authentication.
- Invalid credentials return HTTP 401.
- Authentication credentials are stored as secrets.
- Missing authentication fails closed.

### Boundary B — Authentication -> Authorization

An authenticated identity does not automatically receive every permission.

Required controls:

- Explicit role-to-permission mapping.
- Unknown roles are denied.
- Missing permissions return HTTP 403.
- Administrative capabilities require explicit permissions.

### Boundary C — HTTP Input -> Application Models

HTTP request data is untrusted.

Required controls:

- Pydantic validation.
- Unknown fields rejected.
- String and collection limits.
- Numeric bounds.
- Required field relationships.
- Enum restrictions.

### Boundary D — AI Investigation -> Tool Registry

AI-generated tool requests are untrusted.

Required controls:

- Explicit tool allowlist.
- Explicit argument allowlist.
- Argument count limits.
- String length limits.
- Collection limits.
- Nesting-depth limits.
- Handler exceptions are contained.
- Handler result identity is verified.
- Tool access fails closed.

### Boundary E — Payment Provider -> Webhook Service

Payment-provider webhook traffic is externally supplied data.

Required controls:

- Raw payload signature verification.
- Signature must be valid before acceptance.
- Event ID must be present.
- Previously claimed event IDs are rejected.
- Replay protection is applied before successful acceptance.

### Boundary F — Application -> Financial Gateway

This is the highest-value financial execution boundary.

Sensitive actions must pass through:

1. Actor authorization.
2. Operation authorization.
3. Contract-aware authorization.
4. Financial Guardian evaluation.
5. Final Guardian decision.
6. Gateway execution.

A Guardian decision of `BLOCK` or `REVIEW` must never reach the provider write operation.

---

## 4. Threats and Mitigations

| Threat | Impact | Mitigation |
|---|---|---|
| Missing API credentials | Unauthorized API access | Authentication dependency fails closed |
| Invalid bearer token | Unauthorized API access | Token lookup rejects unknown credentials |
| Privilege escalation | Unauthorized administrative actions | Explicit role-permission matrix |
| Unknown API fields | Parser confusion / injection surface | Pydantic `extra="forbid"` |
| Oversized input | Resource exhaustion | Bounded strings, collections and fields |
| AI tool argument injection | Unauthorized tool behavior | Tool and argument allowlists |
| AI prompt/tool abuse | Unsafe application behavior | Security policy before handler execution |
| AI handler exception leakage | Sensitive information disclosure | Exception containment |
| Forged webhook | False payment state | Provider signature verification |
| Webhook replay | Duplicate processing | Event-ID replay store |
| Unauthorized refund | Financial loss | Contract authorization + refund authorization + Guardian |
| Unauthorized capture | Financial loss | Contract authorization + Guardian |
| Guardian bypass | Financial loss | Protected financial execution service |
| Operation confusion | Wrong financial action | Explicit operation matching |
| Secret leakage in logs | Credential compromise | Recursive sensitive-field redaction |
| Audit manipulation | Loss of accountability | Immutable audit records |
| Unknown authorization role | Privilege escalation | Fail-closed authorization |
| Guardian `REVIEW` treated as approval | Unsafe financial execution | Only `ALLOW` reaches gateway |

---

## 5. Security Invariants

The following invariants must remain true:

1. Unauthenticated API requests cannot reach protected endpoints.
2. Authentication does not imply administrative authorization.
3. Unknown roles are denied.
4. Unknown request fields are rejected.
5. AI tools cannot execute undeclared arguments.
6. AI handler failures do not expose internal exception details.
7. Invalid webhook signatures are never accepted.
8. A previously accepted webhook event cannot be accepted again.
9. A financial action cannot execute with an unauthorized actor.
10. A financial action cannot execute when its operation is unauthorized.
11. A refund above the configured approval threshold requires approval.
12. Guardian `BLOCK` prevents provider execution.
13. Guardian `REVIEW` prevents provider execution.
14. Authorization for one financial operation cannot authorize another operation.
15. Sensitive credentials and webhook secrets are never logged verbatim.

---

## 6. Residual Risks

The current hardening layer does not eliminate every production security risk.

Important residual risks include:

- The in-memory webhook replay store is not suitable as a distributed production
  replay store without shared persistence.
- The current bearer-token foundation is intentionally minimal and should be
  replaced or extended with a production identity provider, key rotation, and
  token lifecycle management.
- Authorization policies should eventually be backed by persisted identity and
  policy management rather than static role definitions.
- Rate limiting and abuse detection should be added at the deployment boundary.
- TLS termination, network isolation, database encryption, backup security, and
  infrastructure IAM remain deployment responsibilities.
- Financial provider credentials require operational rotation and restricted
  infrastructure access.
- Security monitoring should alert on repeated authentication failures,
  authorization failures, webhook failures, and Guardian blocks.
- Dependency and container vulnerability scanning should run in CI/CD.

---

## 7. Security Testing Strategy

Security regression tests should cover:

- Authentication failures.
- Authorization failures.
- Request validation failures.
- Secret leakage prevention.
- AI tool boundary enforcement.
- Webhook authenticity.
- Webhook replay protection.
- Financial authorization.
- Guardian enforcement.
- Operation-confusion prevention.
- Auditability.

Every new sensitive financial capability should add a regression test proving
that its unauthorized path cannot reach the external financial gateway.

---

## 8. Security Review Rule

When adding a new financial write operation, the implementation is incomplete
until the operation has:

- an explicit domain operation,
- an authorization decision,
- a Guardian evaluation,
- a protected application boundary,
- an execution test,
- a denial-path test,
- and an audit trail where required.

Security is therefore treated as an architectural invariant rather than only
an API-layer concern.
