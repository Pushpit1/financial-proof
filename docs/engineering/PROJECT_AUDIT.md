# Project Audit — Financial Proof (`origin/main` @ `80b77b8`)

## 1. Repository & Deployment Topology
- **GitHub Remote**: `https://github.com/Pushpit1/financial-proof.git` (`origin/main`, commit `80b77b8`).
- **Vercel Project**: `pushpits-projects-cb6e0128/financial-proof` (`https://financial-proof.vercel.app`), linked via `.vercel/project.json`.
- **Actual Codebase Layout**:
  - `backend/app/`: FastAPI + Pydantic v2 + SQLAlchemy 2.x + Alembic (11 migrations) + `structlog`.
  - `backend/api/index.py`: Vercel Python serverless entrypoint (`create_app(api_prefix="/api")`).
  - `backend/frontend/`: React 19 + TypeScript + Vite SPA built into `backend/frontend/dist`.
  - `backend/tests/`: 155 test files (`1,187` tests: `1,153` core + `34` benchmarks) — all pass on SQLite (`ruff check app tests` = 0 errors).

## 2. Classification of Existing Capabilities

### Works (Verified)
- `POST /api/contracts/compile`: Deterministic DSL/rule compiler (`DeterministicContractCompiler`).
- `POST /api/simulations`, `attack`, `shrink`, `replay`: Deterministic payment state machine, adversarial attacks (`duplicate`, `out_of_order`, `delayed`, `retry`, `lost_response`, `partial_failure`, `stale_worker_state`, `worker_crash`), and counterexample shrinking.
- `POST /api/verification`: Deterministic before/after snapshot comparison (`VerificationService`).
- `POST /api/webhooks/razorpay`: HMAC-SHA256 signature verification & replay protection (`RazorpayWebhookService`).
- `GET /api/demo/state`, `POST /api/demo/reset`, `replay`: Deterministic demo seed.
- `GET /api/health`: Basic liveness check.

### Broken / Misconfigured
- **Production Database Broken**: Vercel `DATABASE_URL` points to an unreachable/deleted Supabase tenant (`FATAL: (ENOTFOUND) tenant/user postgres.nxmsqgqenfiycdqmxpug not found`), causing `GET /api/proofs` and all DB routes on `https://financial-proof.vercel.app` to return HTTP `500`.
- **Readiness Endpoint**: `GET /api/ready` raises unhandled exception (`500`) instead of `503` structured error when DB is unreachable.
- **Serverless State Loss**: `financial_simulation.py` keeps `_simulations` in an in-memory `dict`, which vanishes across serverless cold starts.
- **Root/Frontend Confusion**: Root `frontend/` contains only an empty `README.md`, while the active frontend lives at `backend/frontend/` (referenced by `package.json` and `backend/vercel.json`).
- **CORS**: `backend/app/main.py` hardcodes `http://localhost:5173` / `http://127.0.0.1:5173` only.

### Missing / Incomplete ("API pending" in UI)
- `GET /contracts` (list contracts — currently `405 Method Not Allowed`), `GET /simulations` (list simulations).
- **Blast Radius API** (`FinancialBlastRadiusAnalyzer` & `BlastRadiusRepository` exist in backend, no HTTP route).
- **AI Investigation API** (`AIInvestigationEngine` & `InvestigationToolRegistry` exist in backend, no HTTP route).
- **Runtime Guardian API** (`FinancialGuardianRuntime` & `FinancialGuardianAuditRepository` exist in backend, no HTTP route).
- **Unified Audit Trail API** (`GET /audit` across guardian, decisions, evaluations, and evidence).
- **Document / Evidence Upload & Extraction** (`CSV`/`JSON`/`PDF`/`TXT` upload with SHA-256 checksum, size/type/path-traversal protection, structured extraction).
- **Reconciliation Engine & Exportable Reports** (JSON / CSV / Markdown / Printable Proof Certificate).
- **Frontend Redesign**: `backend/frontend/src/App.tsx` is a 2,376-line single-file UI titled `<title>frontend</title>` with 4 `"API pending"` tabs and no public landing page, modular component architecture, or responsive polish.
- **Security Enforcement**: `authentication.py` & `authorization.py` exist in `app/api/dependencies/`, not wired to protect endpoints or enforce ownership; missing security headers.
