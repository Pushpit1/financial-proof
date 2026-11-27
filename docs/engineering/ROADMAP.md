# Post-Release Roadmap

1. **Restore Production PostgreSQL Connection**: Replace deleted Supabase `DATABASE_URL` in Vercel environment variables and execute `alembic upgrade head`.
2. **End-to-End Browser Regression Suite**: Add Playwright specs exercising the React workbench flows against a live FastAPI + SQLite/PostgreSQL backend.
3. **External LLM Provider Configuration (Optional)**: Configure `LLM_*` credentials in Vercel if replacing deterministic fallback tool-grounded explanations with a live LLM reasoning adapter while preserving `ai_advisory_only=true`.
4. **Webhook Signature & Settlement Connectors**: Connect live Razorpay/Stripe webhook credentials to feed real-time settlement records into `POST /api/reconciliation/run`.
5. **CI/CD GitHub Actions Verification**: Enforce `ruff check`, `pytest`, and `vite build` on every pull request targeting `main`.
