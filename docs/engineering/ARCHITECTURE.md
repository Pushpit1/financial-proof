# Architecture Overview

## Stack

- **Backend**: FastAPI (`backend/app/main.py`, `backend/api/index.py` for Vercel serverless with `api_prefix="/api"`), Pydantic v2, SQLAlchemy 2 (`NullPool` automatically enabled under `VERCEL`), Alembic (11 migrations in `backend/alembic/versions/`), Python `Decimal` monetary arithmetic.
- **Frontend**: React 19 + TypeScript + Vite 8 + Tailwind CSS v4 + Lucide icons (`backend/frontend/`), compiled to `backend/frontend/dist/`.
- **Deployment**: Vercel (`backend/vercel.json`) building `backend/frontend/` and routing `/api/:path*` to `backend/api/index.py`.

## Core Layers (`backend/app/`)

1. **Domain (`app/domain/`)**: Deterministic payment state machine, financial contracts, constraint evaluator, adversarial fault injector, counterexample shrinker, snapshot verifier, financial blast radius analyzer, bounded AI investigation tool registry, runtime guardian rules, proof evaluator.
2. **Application (`app/application/`)**: Services, ports, and `FinancialGuardianRuntime` coordinating domain rules and repositories.
3. **Database (`app/db/`)**: SQLAlchemy ORM models (`app/db/models/financial.py`), mappers, and repositories with `list_all()` queries for contracts, blast-radius analyses, guardian audits, and evidence.
4. **API (`app/api/routes/`)**:
   - Contracts & Decisions: `/contracts/compile`, `/contracts`, `/contracts/{id}/evaluate`, `/contracts/{id}/decisions`
   - Proofs & Reports: `/proofs`, `/proofs/{id}/evaluate`, `/proofs/{id}/evaluations`, `/proofs/{id}/report?format=json|csv|markdown`
   - Simulations & Counterexamples: `/simulations`, `/simulations/{id}/attacks`, `/simulations/{id}/counterexamples/shrink`, `/verify`
   - Documents & Reconciliation: `/documents/upload`, `/documents`, `/reconciliation/run`
   - Analysis & Governance: `/blast-radius`, `/investigations/tools`, `/investigations`, `/guardian/evaluate`, `/guardian/audit`, `/audit`, `/auth/status`
   - Health & Readiness: `/health`, `/ready`, `/system/status`, `/demo/state`

## Critical Invariant

Deterministic financial evaluation, `Decimal` exposure math, adversarial tracing, and Runtime Guardian enforcement (`ALLOW` / `BLOCK` / `REVIEW`) are strictly separated from AI advisory routes (`/investigations` always returns `ai_advisory_only=true` and `overrides_deterministic_verification=false`).
