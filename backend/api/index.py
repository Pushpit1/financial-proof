"""Vercel entrypoint for the Financial Proof FastAPI application."""

from app.main import create_app

app = create_app(api_prefix="/api")