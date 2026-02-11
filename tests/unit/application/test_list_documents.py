from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from documentor.application.use_cases.list_documents import ListDocuments
from documentor.domain.models.document import Document, SourceType


@pytest.fixture
def uow() -> AsyncMock:
    mock = AsyncMock()
    mock.__aenter__.return_value = mock
    return mock


@pytest.fixture
def use_case(uow: AsyncMock) -> ListDocuments:
    return ListDocuments(uow=uow)


@pytest.mark.asyncio
async def test_execute_should_return_document_list_when_documents_exist(
    use_case: ListDocuments,
    uow: AsyncMock,
) -> None:
    documents = [
        Document(
            id="doc-1",
            source="https://example.com/docs",
            title="Example Docs",
            source_type=SourceType.URL,
            created_at=datetime.now(UTC),
            chunk_count=10,
        ),
        Document(
            id="doc-2",
            source="https://other.com/api",
            title="API Docs",
            source_type=SourceType.URL,
            created_at=datetime.now(UTC),
            chunk_count=5,
        ),
    ]
    uow.documents.list_all.return_value = documents

    result = await use_case.execute()

    assert len(result) == 2
    assert result[0].id == "doc-1"
    assert result[0].title == "Example Docs"
    assert result[0].chunk_count == 10
    assert result[1].id == "doc-2"
    assert result[1].title == "API Docs"


@pytest.mark.asyncio
async def test_execute_should_return_empty_list_when_no_documents(
    use_case: ListDocuments,
    uow: AsyncMock,
) -> None:
    uow.documents.list_all.return_value = []

    result = await use_case.execute()

    assert result == []
    uow.documents.list_all.assert_awaited_once()
