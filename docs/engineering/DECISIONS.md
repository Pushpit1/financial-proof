# Architectural Decisions

1. **Preserve Existing `origin/main` Stack Over Greenfield Rewrite**:
   - Kept the tested FastAPI + SQLAlchemy + Alembic + React/Vite codebase in `backend/`, preserving all 1,187 original tests and clean layered architecture.
2. **Modular Multi-Section Frontend Over Monolithic `App.tsx`**:
   - Replaced the legacy 2,376-line single-file `App.tsx` and its `"API pending"` tabs with typed API clients (`src/api/platform.ts`) and focused sections wired to real endpoints.
3. **Graceful Read/Advisory Degradation When Production DB Is Unreachable**:
   - `/api/ready` explicitly fails closed with HTTP `503` instead of silent fake success or SQLite fallback on serverless storage, while UI sections (`OverviewSection`, `AnalysisGuardianSection`) adapt persistence flags when `systemStatus.database !== "connected"` so deterministic verification, compilation, reconciliation, and advisory tooling remain usable.
4. **Python `NullPool` Under Vercel Serverless**:
   - Avoids exhausting PostgreSQL connection limits across ephemeral Python Lambda instances (`app/db/session.py`).
5. **Bounded AI Investigation Contract**:
   - AI investigation exposes explicit `ai_advisory_only=true` and `overrides_deterministic_verification=false` fields in API payloads and UI displays.
