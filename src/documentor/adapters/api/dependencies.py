from collections.abc import Callable
from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, AsyncSession

from documentor.application.use_cases.ask_question import AskQuestion
from documentor.application.use_cases.ingest_documentation import IngestDocumentation
from documentor.application.use_cases.list_documents import ListDocuments
from documentor.infrastructure.config import Settings
from documentor.infrastructure.database import (
    create_engine as create_db_engine,
    create_session_factory,
)
from documentor.infrastructure.external.anthropic_llm_service import AnthropicLLMService
from documentor.infrastructure.external.file_document_loader import FileDocumentLoader
from documentor.infrastructure.external.http_document_loader import HttpDocumentLoader
from documentor.infrastructure.external.openai_embedding_service import (
    OpenAIEmbeddingService,
)
from documentor.infrastructure.external.openai_llm_service import OpenAILLMService
from documentor.infrastructure.persistence.pg_unit_of_work import PgUnitOfWork


@lru_cache
def get_settings() -> Settings:
    return Settings()


_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_session_factory(
    settings: Annotated[Settings, Depends(get_settings)],
) -> async_sessionmaker[AsyncSession]:
    global _engine, _session_factory
    if _session_factory is None:
        _engine = create_db_engine(settings.database_url)
        _session_factory = create_session_factory(_engine)
    return _session_factory


def _build_ingest_use_case(
    loader: HttpDocumentLoader | FileDocumentLoader,
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
) -> IngestDocumentation:
    return IngestDocumentation(
        loader=loader,
        embedding_service=OpenAIEmbeddingService(
            api_key=settings.openai_api_key,
            model=settings.embedding_model,
        ),
        uow=PgUnitOfWork(session_factory),
    )


def get_ingest_documentation(
    settings: Annotated[Settings, Depends(get_settings)],
    session_factory: Annotated[
        async_sessionmaker[AsyncSession], Depends(get_session_factory)
    ],
) -> IngestDocumentation:
    return _build_ingest_use_case(HttpDocumentLoader(), settings, session_factory)


def get_ask_question(
    settings: Annotated[Settings, Depends(get_settings)],
    session_factory: Annotated[
        async_sessionmaker[AsyncSession], Depends(get_session_factory)
    ],
) -> AskQuestion:
    if settings.llm_provider == "anthropic":
        llm_service = AnthropicLLMService(
            api_key=settings.anthropic_api_key,
            model=settings.llm_model,
        )
    else:
        llm_service = OpenAILLMService(
            api_key=settings.openai_api_key,
            model=settings.llm_model,
        )

    return AskQuestion(
        embedding_service=OpenAIEmbeddingService(
            api_key=settings.openai_api_key,
            model=settings.embedding_model,
        ),
        llm_service=llm_service,
        uow=PgUnitOfWork(session_factory),
    )


def get_ingest_file_documentation(
    settings: Annotated[Settings, Depends(get_settings)],
    session_factory: Annotated[
        async_sessionmaker[AsyncSession], Depends(get_session_factory)
    ],
) -> Callable[[bytes, str], IngestDocumentation]:
    def factory(file_content: bytes, filename: str) -> IngestDocumentation:
        loader = FileDocumentLoader(file_content, filename)

        return _build_ingest_use_case(loader, settings, session_factory)

    return factory


def get_list_documents(
    session_factory: Annotated[
        async_sessionmaker[AsyncSession], Depends(get_session_factory)
    ],
) -> ListDocuments:
    return ListDocuments(
        uow=PgUnitOfWork(session_factory),
    )
