"""FastAPI application entry point."""

from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.exception_handlers import (
    domain_error_handler,
    request_validation_error_handler,
    unhandled_exception_handler,
)
from app.api.middleware import CorrelationIDMiddleware
from app.api.router import api_router
from app.core.config import settings
from app.core.errors.domain import DomainError


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Attach standard HTTP security headers to every response."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault(
            "Referrer-Policy",
            "strict-origin-when-cross-origin",
        )
        response.headers.setdefault(
            "Permissions-Policy",
            "camera=(), microphone=(), geolocation=()",
        )
        return response


def create_app(api_prefix: str = "") -> FastAPI:
    """Create and configure the Financial Proof API application."""
    normalized_prefix = api_prefix.rstrip("/")

    app = FastAPI(
        title=settings.app_name or "Financial Proof API",
        version=settings.app_version or "0.1.0",
        debug=settings.debug,
        docs_url=f"{normalized_prefix}/docs" or "/docs",
        redoc_url=f"{normalized_prefix}/redoc" or "/redoc",
        openapi_url=f"{normalized_prefix}/openapi.json" or "/openapi.json",
    )

    @app.get("/")
    def root() -> dict[str, str]:
        """Return the public application identity."""
        return {
            "name": "Financial Proof",
            "version": "0.1.0",
        }

    app.add_exception_handler(
        DomainError,
        domain_error_handler,
    )
    app.add_exception_handler(
        RequestValidationError,
        request_validation_error_handler,
    )
    app.add_exception_handler(
        Exception,
        unhandled_exception_handler,
    )

    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(CorrelationIDMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "https://financial-proof.vercel.app",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(
        api_router,
        prefix=normalized_prefix,
    )

    return app


app = create_app()
