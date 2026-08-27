from fastapi import FastAPI

from app.api.exception_handlers import domain_error_handler
from app.api.middleware import CorrelationIDMiddleware
from app.api.router import api_router
from app.core.config import settings
from app.core.errors.domain import DomainError
from app.core.logging import configure_logging


def create_app() -> FastAPI:
    configure_logging()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        description=(
            "Deterministic financial authority verification infrastructure."
        ),
    )

    app.add_exception_handler(DomainError, domain_error_handler)
    app.add_middleware(CorrelationIDMiddleware)

    @app.get("/")
    async def root() -> dict[str, str]:
        return {
            "name": settings.app_name,
            "version": settings.app_version,
        }

    app.include_router(api_router)

    return app


app = create_app()