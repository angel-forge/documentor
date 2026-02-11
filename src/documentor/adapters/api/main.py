from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from documentor.adapters.api.error_handlers import register_error_handlers
from documentor.adapters.api.routes.documents import router as documents_router
from documentor.adapters.api.routes.health import router as health_router
from documentor.adapters.api.routes.questions import router as questions_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="DocuMentor", lifespan=lifespan)
    register_error_handlers(app)
    app.include_router(health_router)
    app.include_router(documents_router)
    app.include_router(questions_router)
    return app
