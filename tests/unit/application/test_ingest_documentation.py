from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock

import pytest

from documentor.application.dtos import IngestDocumentationInput
from documentor.application.use_cases.ingest_documentation import IngestDocumentation
from documentor.domain.exceptions import DuplicateDocumentError, InvalidDocumentError
from documentor.domain.models.chunk import Embedding
from documentor.domain.models.document import Document, SourceType
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
    mock.count_tokens = Mock(return_value=5)
    return mock


@pytest.fixture
def uow() -> AsyncMock:
    mock = AsyncMock()
    mock.__aenter__.return_value = mock
    mock.documents.save.side_effect = lambda doc: doc
    mock.documents.find_by_source.return_value = None
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
async def test_execute_should_use_embedding_service_token_count_when_creating_chunks(
    use_case: IngestDocumentation,
    embedding_service: AsyncMock,
    uow: AsyncMock,
) -> None:
    embedding_service.count_tokens = Mock(return_value=42)

    input_dto = IngestDocumentationInput(source="https://example.com/docs")
    await use_case.execute(input_dto)

    embedding_service.count_tokens.assert_called()
    saved_chunks = uow.chunks.save_all.call_args[0][0]
    assert saved_chunks[0].content.token_count == 42


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


def _make_existing_document(source: str = "https://example.com/docs") -> Document:
    return Document(
        id="existing-doc-id",
        source=source,
        title="Existing Doc",
        source_type=SourceType.URL,
        created_at=datetime(2024, 1, 1, tzinfo=UTC),
        chunk_count=5,
    )


@pytest.mark.asyncio
async def test_execute_should_raise_duplicate_error_when_source_exists_and_reject(
    use_case: IngestDocumentation,
    uow: AsyncMock,
) -> None:
    uow.documents.find_by_source.return_value = _make_existing_document()

    with pytest.raises(DuplicateDocumentError) as exc_info:
        await use_case.execute(
            IngestDocumentationInput(
                source="https://example.com/docs", on_duplicate="reject"
            )
        )

    assert "https://example.com/docs" in str(exc_info.value)


@pytest.mark.asyncio
async def test_execute_should_return_existing_document_when_source_exists_and_skip(
    use_case: IngestDocumentation,
    uow: AsyncMock,
    loader: AsyncMock,
) -> None:
    existing = _make_existing_document()
    uow.documents.find_by_source.return_value = existing

    result = await use_case.execute(
        IngestDocumentationInput(source="https://example.com/docs", on_duplicate="skip")
    )

    assert result.document.id == "existing-doc-id"
    assert result.document.title == "Existing Doc"
    assert result.chunks_created == 0
    loader.load.assert_not_awaited()


@pytest.mark.asyncio
async def test_execute_should_replace_document_when_source_exists_and_replace(
    use_case: IngestDocumentation,
    uow: AsyncMock,
    loader: AsyncMock,
) -> None:
    existing = _make_existing_document()
    uow.documents.find_by_source.return_value = existing

    result = await use_case.execute(
        IngestDocumentationInput(
            source="https://example.com/docs", on_duplicate="replace"
        )
    )

    uow.chunks.delete_by_document_id.assert_awaited_once_with("existing-doc-id")
    uow.documents.delete.assert_awaited_once_with("existing-doc-id")
    loader.load.assert_awaited_once()
    assert result.chunks_created == 1
    assert result.document.title == "Test Doc"


@pytest.mark.asyncio
async def test_execute_should_proceed_normally_when_source_is_new(
    use_case: IngestDocumentation,
    uow: AsyncMock,
    loader: AsyncMock,
) -> None:
    uow.documents.find_by_source.return_value = None

    result = await use_case.execute(
        IngestDocumentationInput(source="https://example.com/docs")
    )

    uow.documents.find_by_source.assert_awaited_once_with("https://example.com/docs")
    loader.load.assert_awaited_once()
    assert result.chunks_created == 1


@pytest.mark.asyncio
async def test_execute_should_raise_error_when_loaded_content_is_empty(
    use_case: IngestDocumentation,
    loader: AsyncMock,
    uow: AsyncMock,
) -> None:
    loader.load.return_value = LoadedDocument(
        content="",
        title="Empty Doc",
        source_type=SourceType.URL,
    )

    with pytest.raises(InvalidDocumentError, match="No extractable content"):
        await use_case.execute(
            IngestDocumentationInput(source="https://example.com/empty")
        )

    uow.documents.save.assert_not_awaited()


@pytest.mark.asyncio
async def test_execute_should_raise_error_when_loaded_content_is_whitespace(
    use_case: IngestDocumentation,
    loader: AsyncMock,
    uow: AsyncMock,
) -> None:
    loader.load.return_value = LoadedDocument(
        content="   \n\t  ",
        title="Whitespace Doc",
        source_type=SourceType.URL,
    )

    with pytest.raises(InvalidDocumentError, match="No extractable content"):
        await use_case.execute(
            IngestDocumentationInput(source="https://example.com/blank")
        )

    uow.documents.save.assert_not_awaited()
