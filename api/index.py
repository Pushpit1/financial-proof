"""Vercel entrypoint for the Financial Proof FastAPI application."""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI

BACKEND_ROOT = Path(__file__).resolve().parents[1] / "backend"

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.main import app as backend_app

app = FastAPI(
    title="Financial Proof Vercel API",
    version="0.1.0",
)

app.mount("/api", backend_app)
