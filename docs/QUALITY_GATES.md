# Quality gates

## Latest local verification

| Area | Command | Result |
|---|---|---|
| Backend tests and coverage | `python -m pytest -q --cov=app --cov-report=term-missing` from `backend` | 1,188 passed; 90.72% coverage; one Starlette/AnyIO deprecation warning. |
| Backend lint | `python -m ruff check .` from `backend` | Passed. |
| Python compilation | `python -m compileall -q app tests` from `backend` | Passed. |
| Alembic | `python -m alembic heads` from `backend` | One head: `b1c2d3e4f5a6`. |
| Frontend lint | `npm run lint` from `backend/frontend` | Passed (Oxlint). |
| Frontend production build | `npm run build` from `backend/frontend` | Passed (TypeScript and Vite). |
| Dependency audit | `npm audit --audit-level=high` from `backend/frontend` | Zero findings. |
| Browser readiness | Local Vite + FastAPI, in-memory SQLite | Workbench showed “System ready” with API available and “System unavailable” when the API was stopped. |

Backend tests redirect benchmark results to temporary directories and assert the expected output files are produced. The checked-in benchmark results were not changed by the latest test run.

## Not verified locally

- PostgreSQL integration against a local database; Docker daemon was unavailable.
- Authenticated user journeys; no provider/test identity is configured.
- Full document-upload, verification, audit-export, or multi-tenant end-to-end journeys.
- A Vercel preview or production deployment from this branch.
- Cross-browser, tablet/mobile, and automated accessibility coverage.

The last recorded GitHub Actions run on `main` (2026-09-06) succeeded. It predates the current local changes and does not replace a fresh CI run.
