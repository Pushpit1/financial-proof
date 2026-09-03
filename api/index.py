"""Vercel entrypoint for the Financial Proof FastAPI application."""

from __future__ import annotations

import sys
from pathlib import Path

from starlette.types import ASGIApp, Receive, Scope, Send

BACKEND_ROOT = Path(__file__).resolve().parents[1] / "backend"

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.main import app as fastapi_app


class StripAPIPrefix:
    """Remove Vercel's /api prefix before FastAPI routing."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] == "http":
            path = scope.get("path", "")

            if path == "/api":
                scope = dict(scope)
                scope["path"] = "/"
                scope["raw_path"] = b"/"

            elif path.startswith("/api/"):
                scope = dict(scope)
                stripped_path = path[4:] or "/"
                scope["path"] = stripped_path
                scope["raw_path"] = stripped_path.encode()

        await self.app(scope, receive, send)


app = StripAPIPrefix(fastapi_app)
