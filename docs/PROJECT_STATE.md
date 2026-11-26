# Project state

## Current checkout

- Repository: `Pushpit1/financial-proof`
- Branch: `pushpit1-install-copilot-tooling`
- Base commit: `80b77b8346e6b4266b46a500f907c08d9b7c7852`
- Runtime: FastAPI/Python backend, React/Vite frontend, PostgreSQL persistence, Vercel deployment.
- The M25 implementation and later deployment fixes are in the current Git history. Production readiness is currently blocked; see [deployment status](DEPLOYMENT_STATUS.md).
- A Vercel preview was automatically created from the pushed branch. Production has not been changed.

## Milestones

M18–M25 have explicit milestone commits. The canonical M0–M25 acceptance document was not found. M0–M17 mappings in [roadmap status](ROADMAP_STATUS.md) are therefore inferred from commit chronology and are not represented as authoritative acceptance criteria.

- Latest named milestone commit: M25, `8987a04`.
- M24 Task 10 submission packaging is reported as intentionally deferred; its original task definition was not found.
- Next exact engineering task: diagnose the production database connection failure. Production release also requires an approved authentication-provider decision.

## Architecture and important paths

- `backend/app/domain/`: financial domain models and deterministic rules.
- `backend/app/application/`: services, DTOs, and ports.
- `backend/app/infrastructure/` and `backend/app/db/`: persistence adapters, SQLAlchemy, and database session setup.
- `backend/app/api/`: FastAPI routes, dependencies, middleware, and error handling.
- `backend/api/index.py`, `backend/vercel.json`: Vercel API entry point and deployment configuration.
- `backend/frontend/`: React/Vite verification workbench.
- `backend/tests/`: backend unit, integration, and regression tests.
- `backend/benchmarks/`: benchmark implementations and checked-in reference output.
- `backend/docs/security/threat-model.md`: existing security threat model.

## Latest verified quality gates

- Backend: 1,188 passed; 90.72% coverage; Ruff, Python compilation, and Alembic-head checks passed.
- Frontend: Oxlint and production build passed; `npm audit --audit-level=high` reported zero vulnerabilities.
- Browser: local workbench displayed both database-ready and backend-unavailable states against the real readiness endpoint.
- One existing Starlette/AnyIO deprecation warning remains.

Exact commands and limitations are in [quality gates](QUALITY_GATES.md).

## Blockers and next actions

1. Investigate the production `psycopg.OperationalError`; production `/api/ready` still returns 500. The latest branch preview also returns API 500 because `API_AUTH_TOKEN` is not configured in Vercel Preview.
2. Select an approved identity provider before wiring production authentication. Business API routes currently do not depend on the existing authentication helper; do not expose the server bearer token to the browser.
3. Recover the authoritative M0–M25 roadmap and M24 Task 10 definition if exact acceptance status or packaging work is required.
4. Move or consolidate frontend CI under the root `.github/workflows/` directory, then add browser end-to-end coverage.
