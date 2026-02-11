from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from documentor.domain.exceptions import (
    DocumentLoadError,
    DocumentNotFoundError,
    DuplicateDocumentError,
    EmbeddingGenerationError,
    InvalidChunkError,
    InvalidDocumentError,
    InvalidQuestionError,
    LLMGenerationError,
)

_EXCEPTION_STATUS_MAP: dict[type[Exception], int] = {
    InvalidQuestionError: 400,
    InvalidDocumentError: 400,
    InvalidChunkError: 400,
    DocumentNotFoundError: 404,
    DuplicateDocumentError: 409,
    DocumentLoadError: 502,
    EmbeddingGenerationError: 502,
    LLMGenerationError: 502,
}


def register_error_handlers(app: FastAPI) -> None:
    for exc_class, status_code in _EXCEPTION_STATUS_MAP.items():

        def _make_handler(status: int):  # noqa: ANN001, ANN202
            async def handler(request: Request, exc: Exception) -> JSONResponse:
                return JSONResponse(status_code=status, content={"detail": str(exc)})

            return handler

        app.add_exception_handler(exc_class, _make_handler(status_code))
