from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from documentor.domain.exceptions import (
    DocumentLoadError,
    DocumentNotFoundError,
    DuplicateDocumentError,
    EmbeddingGenerationError,
    InvalidAnswerError,
    InvalidChunkError,
    InvalidDocumentError,
    InvalidQuestionError,
    LLMGenerationError,
)

_EXCEPTION_STATUS_MAP: dict[type[Exception], int] = {
    InvalidQuestionError: 400,
    InvalidDocumentError: 400,
    InvalidChunkError: 400,
    InvalidAnswerError: 400,
    DocumentNotFoundError: 404,
    DuplicateDocumentError: 409,
    DocumentLoadError: 502,
    EmbeddingGenerationError: 502,
    LLMGenerationError: 502,
}

_SAFE_MESSAGES: dict[type[Exception], str] = {
    DocumentLoadError: "Failed to load the document from the given source",
    EmbeddingGenerationError: "Embedding generation service is currently unavailable",
    LLMGenerationError: "Language model service is currently unavailable",
}


def register_error_handlers(app: FastAPI) -> None:
    for exc_class, status_code in _EXCEPTION_STATUS_MAP.items():

        def _make_handler(status: int):  # noqa: ANN001, ANN202
            async def handler(request: Request, exc: Exception) -> JSONResponse:
                detail = _SAFE_MESSAGES.get(type(exc), str(exc))
                return JSONResponse(status_code=status, content={"detail": detail})

            return handler

        app.add_exception_handler(exc_class, _make_handler(status_code))
