import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from documentor.domain.models.document import Document, SourceType
from documentor.infrastructure.persistence.pg_document_repository import (
    PgDocumentRepository,
)


@pytest.fixture
def repository(
    session_factory: async_sessionmaker[AsyncSession],
) -> PgDocumentRepository:
    return PgDocumentRepository(session_factory)


@pytest.mark.asyncio
async def test_save_should_persist_document_when_valid(
    repository: PgDocumentRepository,
) -> None:
    document = Document.create(
        source="https://example.com/docs",
        title="Example Docs",
        source_type=SourceType.URL,
        chunk_count=5,
    )

    saved = await repository.save(document)

    assert saved.id == document.id
    found = await repository.find_by_id(document.id)
    assert found is not None
    assert found.id == document.id
    assert found.source == "https://example.com/docs"
    assert found.title == "Example Docs"
    assert found.source_type == SourceType.URL
    assert found.chunk_count == 5


@pytest.mark.asyncio
async def test_find_by_id_should_return_none_when_not_found(
    repository: PgDocumentRepository,
) -> None:
    result = await repository.find_by_id("nonexistent-id")
    assert result is None


@pytest.mark.asyncio
async def test_list_all_should_return_all_saved_documents(
    repository: PgDocumentRepository,
) -> None:
    doc1 = Document.create(
        source="https://example.com/a",
        title="Doc A",
        source_type=SourceType.URL,
    )
    doc2 = Document.create(
        source="/path/to/file.md",
        title="Doc B",
        source_type=SourceType.FILE,
    )

    await repository.save(doc1)
    await repository.save(doc2)

    documents = await repository.list_all()
    ids = {d.id for d in documents}
    assert doc1.id in ids
    assert doc2.id in ids
