from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from documentor.adapters.api.dependencies import get_settings
from documentor.adapters.api.error_handlers import register_error_handlers
from documentor.adapters.api.routes.documents import router as documents_router
from documentor.adapters.api.routes.health import router as health_router
from documentor.adapters.api.routes.questions import router as questions_router
from documentor.infrastructure.persistence.orm_models import EMBEDDING_DIMENSION


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    if settings.embedding_dimension != EMBEDDING_DIMENSION:
        raise RuntimeError(
            f"Settings embedding_dimension={settings.embedding_dimension} does not "
            f"match the database column dimension={EMBEDDING_DIMENSION}. "
            f"Update EMBEDDING_DIMENSION in orm_models.py and create a migration."
        )
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="DocuMentor", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_error_handlers(app)
    app.include_router(health_router)
    app.include_router(documents_router)
    app.include_router(questions_router)
    return app
