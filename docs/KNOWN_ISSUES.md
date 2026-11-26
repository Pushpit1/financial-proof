# Known issues

## Release blockers

- **Production database readiness fails.** The deployed `/api/ready` returned HTTP 500 with `psycopg.OperationalError`; the existing database is hosted on Supabase, but available logs did not identify the root cause or expose credentials. The local route now maps SQLAlchemy failures to HTTP 503, but this does not repair connectivity and has not been deployed.
- **Business API authentication is not wired.** Authentication dependencies exist, but business routes do not use them. No identity provider was identified, and the frontend has no login. Do not deploy sensitive business APIs as production-ready or send `API_AUTH_TOKEN` to the browser.
- **M24 Task 10 remains deferred.** Prior user-provided history says submission packaging was deferred. The original task description and acceptance criteria are unavailable.

## Quality and product gaps

- **Frontend CI is not discovered by GitHub Actions.** The root workflow is `.github/workflows/ci.yml`; the separate frontend workflow is under `backend/.github/workflows/`, which is not the repository's root workflow directory.
- **No Playwright/browser test suite is installed.** The local readiness states were checked in a real browser, but the full user journeys have not been automated.
- **No general evidence-document upload/extraction route was found.** Current evidence handling is structured/API-based; do not claim document ingestion is supported.
- **Local PostgreSQL integration was not run.** The Docker daemon was unavailable, and the production database is currently unreachable. The latest recorded CI run on `main` passed, but that does not resolve the present deployment failure.
- **README documentation references were stale.** The documentation map is being replaced with files that exist in this repository.

These are observed gaps or blockers, not claims of regulatory non-compliance. No certification or compliance status is asserted.
