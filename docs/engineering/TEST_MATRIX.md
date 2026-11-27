# Test Matrix

| Suite / Command | Scope | Environment | Outcome |
| --- | --- | --- | --- |
| `python -m ruff check app tests` | Backend formatting & lint rules (`E, F, I, B, UP`) | Windows Python 3.14 | Passed (`All checks passed!`) |
| `python -m alembic upgrade head` | All 11 schema migrations (`5e3161c065ab` -> `b1c2d3e4f5a6`) | Fresh SQLite DB | Passed (exit 0) |
| `python -m pytest tests/test_platform_api_extensions.py -v` | Blast radius, investigations, guardian, docs upload & traversal block, reconciliation, proof reports, audit, headers | FastAPI `TestClient` + SQLite | Passed (`8 passed`) |
| `python -m pytest -q` | Full backend unit, API, security, configuration & benchmark suites | SQLite (`DATABASE_URL=sqlite:///./...`) | Passed (`1195 passed`) |
| `tsc -b && vite build` (`backend/frontend/`) | TypeScript strict typecheck + Vite 8 production bundle | Node.js 24 | Passed (0 errors) |
| Live local `uvicorn` HTTP E2E script | Live FastAPI HTTP endpoints, security headers, proof creation, markdown export, audit log | `uvicorn app.main:app` + SQLite | Passed |
| Live Vercel Production HTTP probes | `https://financial-proof.vercel.app` `/` and `/api/*` endpoints | Vercel Production (`iad1`/`las1`/`bom1`) | Frontend + stateless API `200 OK`; `/api/ready` `503` (Supabase DNS unreachable) |
