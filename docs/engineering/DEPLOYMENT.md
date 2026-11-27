# Deployment Runbook

## Current Production Deployment

- **Platform**: Vercel (`pushpits-projects-cb6e0128/financial-proof`, `prj_vZ5SU1tVzzKyRvfdYO7zUPyEdgQ9`)
- **Primary URL**: `https://financial-proof.vercel.app`
- **Root Directory**: `backend` (`backend/vercel.json`)
- **Build Steps**:
  1. `cd frontend && npm install && npm run build` -> outputs `backend/frontend/dist/`
  2. Python 3.12 serverless function bundles `backend/api/index.py` via `backend/pyproject.toml` (`NullPool` enabled when `VERCEL` env var is set)

## External Database Blocker & Remediation

Currently `GET /api/ready` returns `503 Database connection is unavailable.` and `GET /api/system/status` reports `database: "unreachable"` (`OperationalError`). Prior Vercel logs showed the configured Supabase connection string targets `postgres.nxmsqgqenfiycdqmxpug`, returning `FATAL: (ENOTFOUND) tenant/user postgres.nxmsqgqenfiycdqmxpug not found`.

To restore full DB persistence in production:
1. Provision or restore an active PostgreSQL database (Supabase, Neon, RDS, etc.).
2. Update `DATABASE_URL` in Vercel project environment variables (`vercel env add DATABASE_URL production`).
3. Run schema migrations against the production database: `alembic upgrade head`.
4. Verify `GET https://financial-proof.vercel.app/api/ready` returns `200 {"status":"ready"}`.
