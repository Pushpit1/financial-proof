# Security Architecture & Controls

## Implemented Controls

- **Fail-Closed Production Auth (`app/core/config.py`)**: Production environment requires `API_AUTH_TOKEN` and `DEBUG=false`. Public UI status is exposed cleanly via `GET /api/auth/status` without revealing token values.
- **HTTP Security Headers (`SecurityHeadersMiddleware` in `app/main.py`)**:
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - `Permissions-Policy: camera=(), microphone=(), geolocation=()`
- **CORS Restrictions**: Configured to allow explicit origins (`https://financial-proof.vercel.app`, `http://localhost:5173`, `http://localhost:3000`) plus configured environment origins.
- **Secure Document Ingestion (`app/api/routes/documents.py`)**:
  - Enforces 5 MB maximum upload size (`413` on overflow).
  - Enforces `.csv`, `.json`, `.txt`, `.pdf` allowlist (`400` on unsupported extension).
  - Strips directory paths (`Path(raw_name).name`) and rejects traversal patterns (`..`, `/`, `\`).
  - Computes SHA-256 digests and flags duplicate checksum uploads.
- **Financial & AI Separation**: Monetary sums use Python `Decimal` / integer minor units. AI investigation returns read-only advisory output (`ai_advisory_only=true`, `overrides_deterministic_verification=false`).
- **Secrets Hygiene**: `.env`, `.env.*` (except `.env.example`), `*.db`, and build caches are excluded via `.gitignore` and `backend/.vercelignore`.
