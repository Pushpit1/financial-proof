# Roadmap status

## Evidence note

No canonical roadmap document defining all M0–M25 acceptance criteria was found in the repository or reachable Git history. Commits explicitly name M18–M25 only. M0–M17 below are conservative, inferred groupings of the chronological implementation history; they are marked **Partially complete** because their exact acceptance criteria cannot be verified. Do not treat the inferred names as the locked roadmap.

| Milestone | Inferred or recorded scope | Status | Evidence and remaining work |
|---|---|---|---|
| M0 | Repository and typed configuration foundation | Partially complete | `c9bab39`, `2facbc8`; recover official acceptance criteria. |
| M1 | PostgreSQL, Alembic, API schema and router foundation | Partially complete | `47ee3ba`, `6eb2640`; recover official acceptance criteria. |
| M2 | Domain errors, structured logging, request correlation, container and CI foundation | Partially complete | `33d1d18`–`8d9e14b`; recover official acceptance criteria. |
| M3 | Financial value objects and proof domain services | Partially complete | `dee2b72`, `029ae6d`; recover official acceptance criteria. |
| M4 | Persistence models, migrations, repositories, Unit of Work, and application services | Partially complete | `0ed3ee2`–`e8b34a8`; verify against the missing milestone definition. |
| M5 | Financial-proof API creation, retrieval, and evaluation | Partially complete | `f05fd7b`–`e3ff896`; verify exact acceptance criteria. |
| M6 | Deterministic proof rules and idempotent evaluation | Partially complete | `8ea36ad`–`7f26c59`; verify exact acceptance criteria. |
| M7 | Configurable proof policy, confidence thresholds, and configuration validation | Partially complete | `dc3e4b6`–`5964d4a`; verify exact acceptance criteria. |
| M8 | Deterministic explanations and immutable evaluation results | Partially complete | `89a262f`–`6ed3995`; verify exact acceptance criteria. |
| M9 | Persisted evaluation history, retrieval, and deterministic ordering | Partially complete | `2c94bbc`–`c72ade1`; verify exact acceptance criteria. |
| M10 | Financial Contract authority, versioning, and evidence linking | Partially complete | `d3f7b38`, `b9ae088`, `bdae687`; verify exact acceptance criteria. |
| M11 | Contract rules, structured conditions, constraints, and validation | Partially complete | `c80ac5a`–`fea7e64`; verify exact acceptance criteria. |
| M12 | Deterministic contract evaluation and explanations | Partially complete | `17f8016`–`e5c55e6`; verify exact acceptance criteria. |
| M13 | Contract decisions, persistence, and API history | Partially complete | `377cd54`–`381f70d`; verify exact acceptance criteria. |
| M14 | Repository ports and transaction boundaries through Unit of Work | Partially complete | `f22e967`–`992d92d`; verify exact acceptance criteria. |
| M15 | Deterministic payment simulation | Partially complete | `27e0d58`, `119059b`; verify exact acceptance criteria. |
| M16 | Adversarial scenarios and deterministic counterexample shrinking | Partially complete | `24192fd`–`e602b0b`; verify exact acceptance criteria. |
| M17 | Financial blast-radius analysis, AI investigation, and runtime guardian | Partially complete | `a18ffee`, `7d170cd`, `fb1896f`; verify exact acceptance criteria. |
| M18 | Observability and auditability | Verified complete | `43c1227`; current test suite passes. |
| M19 | Security hardening | Verified complete | `93ca18a`; this does not establish certification or prove the current API is protected. |
| M20 | Chaos, property, and regression testing | Verified complete | `bfa424f`; current backend suite passes. |
| M21 | Performance benchmarking | Verified complete | `362592a`; benchmark test output is now isolated to temporary directories. |
| M22 | Frontend dashboard | Verified complete | `126b3a1`; current frontend lint and production build pass. |
| M23 | Demo | Verified complete | `bb4775a`; demo implementation exists in the current source. |
| M24 | Hardening through Task 9 | Partially complete | `bb4775a` states completion through Task 9. Task 10 submission packaging is reported deferred; recover its original definition before resuming it. |
| M25 | Production readiness and final hardening | Blocked | `8987a04` and later Vercel fixes are present, but the live database readiness check returned 500 with `psycopg.OperationalError`. Production authentication is also unresolved. |

## Do not reopen without evidence

M18–M23 have explicit completion commits and current source/test evidence. Reopen them only for a demonstrated regression or a concrete acceptance gap. M25's current production blocker is deployment/database readiness, not a reason to recreate its completed implementation.
