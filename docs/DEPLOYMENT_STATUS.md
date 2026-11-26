# Deployment status

## Existing Vercel deployment

- Existing project: `financial-proof`
- Repository link: `Pushpit1/financial-proof`
- Production URL: [https://financial-proof.vercel.app](https://financial-proof.vercel.app)
- Database provider: Supabase
- Vercel root directory: `backend`
- API deployment configuration: `backend/vercel.json` and `backend/api/index.py`
- Latest production deployment observed: `main` at `80b77b8`
- Branch preview created automatically after pushing `pushpit1-install-copilot-tooling`: [financial-proof-99agvedaq-pushpits-projects-cb6e0128.vercel.app](https://financial-proof-99agvedaq-pushpits-projects-cb6e0128.vercel.app)
- No production deployment was created from this worktree.

## Branch preview

- Deployment state: Ready
- Homepage: HTTP 200
- `/api/health` and `/api/ready`: HTTP 500 because Preview lacks `API_AUTH_TOKEN`, while `APP_ENV` selects production-mode settings validation.
- This is a preview-only configuration issue; no production environment variables were changed.

## Last live checks

- `/`: HTTP 200
- `/api/health`: HTTP 200
- `/api/ready`: HTTP 500 with `psycopg.OperationalError`

The database connection failure's underlying cause was not established from the available deployment logs. The readiness route has since been changed locally to return a non-sensitive HTTP 503 response for SQLAlchemy errors and log only the exception class. That source change has not been deployed; production may still return the prior 500.

## Release blockers

1. Restore and verify production database connectivity, then confirm `/api/ready` succeeds.
2. Select an approved identity provider and wire authentication/authorization through the business API and frontend.
3. Configure an approved, non-production API token for Preview or change preview-mode configuration deliberately; do not copy production credentials into Preview.
4. Pass the repository's backend and frontend gates plus preview-environment smoke tests before any production deployment.

The existing project had environment variable names for `DATABASE_URL`, `API_AUTH_TOKEN`, `SECRET_KEY`, payment-provider keys/secrets, and LLM configuration. Values were not read or recorded here. Do not place server secrets in Vite/client environment variables.
