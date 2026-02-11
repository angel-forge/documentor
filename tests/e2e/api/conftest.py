from collections.abc import AsyncIterator
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from documentor.adapters.api.dependencies import (
    get_ask_question,
    get_ingest_documentation,
    get_list_documents,
)
from documentor.adapters.api.main import create_app
from documentor.application.dtos import (
    AnswerDTO,
    DocumentDTO,
    IngestResultDTO,
    SourceReferenceDTO,
)


@pytest.fixture
def mock_ingest_documentation() -> AsyncMock:
    mock = AsyncMock()
    mock.execute.return_value = IngestResultDTO(
        document=DocumentDTO(
            id="doc-1",
            source="https://example.com/docs",
            title="Example Docs",
            source_type="url",
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            chunk_count=3,
        ),
        chunks_created=3,
    )
    return mock


@pytest.fixture
def mock_ask_question() -> AsyncMock:
    mock = AsyncMock()
    mock.execute.return_value = AnswerDTO(
        text="The answer is 42.",
        sources=[
            SourceReferenceDTO(
                document_title="Example Docs",
                chunk_text="Relevant chunk text",
                relevance_score=0.95,
                chunk_id="chunk-1",
            ),
        ],
    )
    return mock


@pytest.fixture
def mock_list_documents() -> AsyncMock:
    mock = AsyncMock()
    mock.execute.return_value = [
        DocumentDTO(
            id="doc-1",
            source="https://example.com/docs",
            title="Example Docs",
            source_type="url",
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            chunk_count=3,
        ),
    ]
    return mock


@pytest_asyncio.fixture
async def client(
    mock_ingest_documentation: AsyncMock,
    mock_ask_question: AsyncMock,
    mock_list_documents: AsyncMock,
) -> AsyncIterator[AsyncClient]:
    app = create_app()
    app.dependency_overrides[get_ingest_documentation] = lambda: (
        mock_ingest_documentation
    )
    app.dependency_overrides[get_ask_question] = lambda: mock_ask_question
    app.dependency_overrides[get_list_documents] = lambda: mock_list_documents

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
