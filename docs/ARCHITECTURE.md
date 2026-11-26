# Architecture

## Runtime shape

Financial Proof is a modular application, not a set of microservices. The existing stack is Python/FastAPI, SQLAlchemy/Alembic, PostgreSQL, and a React/Vite frontend.

- `backend/app/main.py` creates the FastAPI application, registers middleware and exception handlers, and mounts the API router.
- `backend/app/api/router.py` aggregates health, contract, proof, simulation, verification, webhook, and demo routes.
- `backend/api/index.py` creates the Vercel app with the `/api` prefix. `backend/vercel.json` configures the existing deployment.
- `backend/frontend/` contains the single-page workbench. Its Vite development proxy rewrites `/api/*` to the local FastAPI routes.
- `backend/app/domain/` holds domain models and deterministic rules; `application/` contains use cases, DTOs, and ports; `infrastructure/` and `db/` provide persistence adapters and database setup.

## Verification flow

The current product accepts structured proof, claim, evidence, contract, and simulation inputs through API routes. Application services coordinate domain evaluation and persistence; domain rules produce deterministic decisions and explanations; persisted history and evidence references support later inspection. Contract decisions and evaluation history are available through the existing API.

The inspected route surface does not provide a general document-upload or extraction workflow. Do not present document ingestion as implemented.

AI investigation exists as a supporting capability. Deterministic contract/proof evaluation remains the source of financial results; AI output must not be presented as a verified decision.

## Boundaries and operational caveats

- PostgreSQL/SQLAlchemy persistence, Alembic migrations, repositories, and a Unit of Work are present.
- Authentication helpers exist in `backend/app/api/dependencies/authentication.py`, but the business routes do not currently depend on them. There is no selected identity provider or browser login flow.
- The browser must never receive `API_AUTH_TOKEN` or other server secrets.
- `/health` is process health; `/ready` checks database availability. The source now reports 503 on SQLAlchemy readiness failures, while production has not been redeployed with that change.
- See [known issues](KNOWN_ISSUES.md) for deployment, authentication, and CI gaps.
