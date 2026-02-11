from unittest.mock import AsyncMock

import pytest

from documentor.application.dtos import IngestDocumentationInput
from documentor.application.use_cases.ingest_documentation import IngestDocumentation
from documentor.domain.models.chunk import Embedding
from documentor.domain.models.document import SourceType
from documentor.domain.services.document_loader_service import LoadedDocument


@pytest.fixture
def loader() -> AsyncMock:
    mock = AsyncMock()
    mock.load.return_value = LoadedDocument(
        content="word " * 100,
        title="Test Doc",
        source_type=SourceType.URL,
    )
    return mock


@pytest.fixture
def embedding_service() -> AsyncMock:
    mock = AsyncMock()
    mock.embed_batch.return_value = [Embedding.from_list([0.1, 0.2, 0.3])]
    return mock


@pytest.fixture
def uow() -> AsyncMock:
    mock = AsyncMock()
    mock.__aenter__.return_value = mock
    mock.documents.save.side_effect = lambda doc: doc
    mock.chunks.save_all.side_effect = lambda chunks: chunks
    return mock


@pytest.fixture
def use_case(
    loader: AsyncMock,
    embedding_service: AsyncMock,
    uow: AsyncMock,
) -> IngestDocumentation:
    return IngestDocumentation(
        loader=loader,
        embedding_service=embedding_service,
        uow=uow,
    )


@pytest.mark.asyncio
async def test_execute_should_return_result_with_chunks_when_valid_source(
    use_case: IngestDocumentation,
) -> None:
    input_dto = IngestDocumentationInput(source="https://example.com/docs")

    result = await use_case.execute(input_dto)

    assert result.document.title == "Test Doc"
    assert result.document.source == "https://example.com/docs"
    assert result.document.source_type == "url"
    assert result.chunks_created == 1
    assert result.document.chunk_count == 1


@pytest.mark.asyncio
async def test_execute_should_call_loader_and_embedding_service_when_ingesting(
    use_case: IngestDocumentation,
    loader: AsyncMock,
    embedding_service: AsyncMock,
) -> None:
    input_dto = IngestDocumentationInput(source="https://example.com/docs")

    await use_case.execute(input_dto)

    loader.load.assert_awaited_once_with("https://example.com/docs")
    embedding_service.embed_batch.assert_awaited_once()
    texts = embedding_service.embed_batch.call_args[0][0]
    assert len(texts) == 1
    assert isinstance(texts[0], str)


@pytest.mark.asyncio
async def test_execute_should_save_document_and_chunks_when_ingesting(
    use_case: IngestDocumentation,
    uow: AsyncMock,
) -> None:
    input_dto = IngestDocumentationInput(source="https://example.com/docs")

    await use_case.execute(input_dto)

    uow.chunks.save_all.assert_awaited_once()
    saved_chunks = uow.chunks.save_all.call_args[0][0]
    assert len(saved_chunks) == 1
    assert saved_chunks[0].has_embedding()

    uow.documents.save.assert_awaited_once()
    saved_doc = uow.documents.save.call_args[0][0]
    assert saved_doc.title == "Test Doc"
    assert saved_doc.chunk_count == 1


@pytest.mark.asyncio
async def test_execute_should_create_multiple_chunks_for_large_content(
    loader: AsyncMock,
    embedding_service: AsyncMock,
    uow: AsyncMock,
) -> None:
    loader.load.return_value = LoadedDocument(
        content="word " * 1000,
        title="Large Doc",
        source_type=SourceType.URL,
    )
    embedding_service.embed_batch.side_effect = lambda texts: [
        Embedding.from_list([0.1, 0.2, 0.3]) for _ in texts
    ]

    use_case = IngestDocumentation(
        loader=loader,
        embedding_service=embedding_service,
        uow=uow,
    )

    result = await use_case.execute(
        IngestDocumentationInput(source="https://example.com/large")
    )

    assert result.chunks_created > 1
    assert result.document.chunk_count == result.chunks_created


@pytest.mark.asyncio
async def test_execute_should_save_document_before_chunks(
    use_case: IngestDocumentation,
    uow: AsyncMock,
) -> None:
    call_order: list[str] = []
    uow.documents.save.side_effect = lambda doc: call_order.append("document")
    uow.chunks.save_all.side_effect = lambda chunks: call_order.append("chunks")

    input_dto = IngestDocumentationInput(source="https://example.com/docs")
    await use_case.execute(input_dto)

    assert call_order == ["document", "chunks"]
