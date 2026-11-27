# Project State

## Summary

- **Repository**: `C:\Users\pushp\Documents\financial-proof`
- **Branch**: `main` (tracking `origin/main` at commit `80b77b8` prior to release commit)
- **Production URL**: `https://financial-proof.vercel.app`
- **Vercel Project ID**: `prj_vZ5SU1tVzzKyRvfdYO7zUPyEdgQ9` (root directory: `backend`)

## Verified Runtime Status

- **Backend Unit + Integration + Benchmark Suite**: `1195 passed` (`python -m pytest -q` against clean SQLite with all 11 Alembic migrations applied via `python -m alembic upgrade head`).
- **Static Lint & Types**: `python -m ruff check app tests` (`All checks passed!`), `tsc -b && vite build` (`0` errors, bundle built to `backend/frontend/dist/`).
- **Live Vercel Production**:
  - Frontend `/` returns `200 OK`.
  - Compute-backed & security routes (`/api/health`, `/api/system/status`, `/api/auth/status`, `/api/contracts/compile`, `/api/blast-radius` with `persist=false`, `/api/investigations/tools`, `/api/investigations`, `/api/guardian/evaluate` with `persist_audit=false`, `/api/reconciliation/run`) return `200 OK` with security headers (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`).
  - Readiness route `/api/ready` returns `503 Service Unavailable` cleanly because the external Supabase PostgreSQL host configured in Vercel's `DATABASE_URL` (`postgres.nxmsqgqenfiycdqmxpug`) fails DNS/tenant resolution (`ENOTFOUND tenant/user postgres.nxmsqgqenfiycdqmxpug not found`).
  - Database-backed routes (`/api/proofs`, `/api/contracts`, `/api/documents`, `/api/audit`, `persist=true`) require restoring a valid PostgreSQL `DATABASE_URL` in Vercel environment variables and running `alembic upgrade head`.
