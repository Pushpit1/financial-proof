"""FastAPI application entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.exception_handlers import domain_error_handler
from app.api.middleware import CorrelationIDMiddleware
from app.api.router import api_router
from app.core.config import settings
from app.core.errors.domain import DomainError


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
    )

    app.add_exception_handler(
        DomainError,
        domain_error_handler,
    )

    app.add_middleware(
        CorrelationIDMiddleware,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)

    @app.get("/")
    async def root() -> dict[str, str]:
        """Return basic application metadata."""

        return {
            "name": settings.app_name,
            "version": settings.app_version,
        }

    return app


app = create_app()
