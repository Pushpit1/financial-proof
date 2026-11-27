# Feature Status Matrix

| Area | Backend API | Frontend UI | Persisted DB Support | Notes |
| --- | --- | --- | --- | --- |
| Public Landing & Shell Navigation | Live (`/system/status`, `/health`) | Live (`LandingView`, `AppShell`) | Optional | Graceful `database=unreachable` status badge |
| Financial Contract Compiler & Evaluator | Live (`/contracts/compile`, `/contracts`, `/contracts/{id}/evaluate`) | Live (`ContractsSection`) | Ready (Alembic) | Natural-language rule compilation + DB persistence |
| Document Upload & Extraction | Live (`/documents/upload`, `/documents`) | Live (`DocumentsSection`) | Ready (Alembic) | 5 MB limit, `.csv/.json/.txt/.pdf`, path traversal block, SHA-256 duplicate check |
| Deterministic Ledger Reconciliation | Live (`/reconciliation/run`) | Live (`DocumentsSection`) | Stateless / Evidence | Exact `Decimal` discrepancy & exposure math |
| Payment Simulation & Adversarial Attacks | Live (`/simulations`, `/attacks`, `/counterexamples/shrink`) | Live (`SimulationsSection`) | Ready (Alembic) | All 8 attack types + trace minimization |
| Snapshot Verification & Financial Proofs | Live (`/verify`, `/proofs`, `/evaluate`, `/report`) | Live (`VerificationProofSection`) | Ready (Alembic) | Exports `json`, `csv`, and `markdown` reports |
| Financial Blast Radius | Live (`/blast-radius`) | Live (`AnalysisGuardianSection`) | Ready (Alembic) | Repaired broken `app.db.models.financial_blast_radius` import |
| Bounded AI Investigation | Live (`/investigations`, `/investigations/tools`) | Live (`AnalysisGuardianSection`) | Read-only | Enforces `ai_advisory_only=true`, `overrides_deterministic_verification=false` |
| Runtime Guardian & Unified Audit | Live (`/guardian/evaluate`, `/guardian/audit`, `/audit`) | Live (`AnalysisGuardianSection`, `AuditSettingsSection`) | Ready (Alembic) | Evaluates policies deterministically & logs audits |
| Auth & Security Middleware | Live (`/auth/status`, `SecurityHeadersMiddleware`) | Live (`AuditSettingsSection`) | N/A | Bearer auth fail-closed in production when configured |
