# Decisions

| Decision | Rationale and current consequence |
|---|---|
| Financial Contracts are the central financial authority. | Contracts and their versions state the rules that apply to a financial operation. Preserve deterministic, explicit evaluation and historical version references. |
| Deterministic logic, not AI, decides financial outcomes. | AI may assist with extraction, investigation, or explanations, but must not silently replace reproducible rule evaluation. |
| Preserve the existing modular FastAPI/PostgreSQL architecture. | Existing domain, application, persistence, repository, and Unit of Work boundaries are established and tested. No evidence currently justifies a rewrite or additional service infrastructure. |
| Keep the existing Vercel project. | The `financial-proof` project already links to `Pushpit1/financial-proof`; duplicate project or infrastructure creation is out of scope. |
| Do not choose an identity provider by assumption. | The user could not identify an existing provider. Production authentication design remains blocked; do not invent an integration or expose a bearer secret in the frontend. |
| Do not deploy production while readiness or authentication is unresolved. | The live readiness endpoint failed with `psycopg.OperationalError`, and the business API routes are not wired to authentication dependencies. |
| Treat M0–M17 names and acceptance criteria as unresolved. | The canonical roadmap was not found. The history supports inferred implementation groupings, not authoritative completion claims. |
| Keep benchmark tests from writing into checked-in result files. | Tests patch each benchmark's `RESULTS_PATH` to `tmp_path` and assert output persistence there, preserving repository data while retaining the benchmark behavior check. |
