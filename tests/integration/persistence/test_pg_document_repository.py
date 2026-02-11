import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from documentor.domain.models.document import Document, SourceType
from documentor.infrastructure.persistence.pg_document_repository import (
    PgDocumentRepository,
)


@pytest_asyncio.fixture
async def session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncSession:
    session = session_factory()
    yield session
    await session.close()


@pytest.fixture
def repository(session: AsyncSession) -> PgDocumentRepository:
    return PgDocumentRepository(session)


@pytest.mark.asyncio
async def test_save_should_persist_document_when_valid(
    repository: PgDocumentRepository,
    session: AsyncSession,
) -> None:
    document = Document.create(
        source="https://example.com/docs",
        title="Example Docs",
        source_type=SourceType.URL,
        chunk_count=5,
    )

    saved = await repository.save(document)
    await session.commit()

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
async def test_find_by_ids_should_return_matching_documents_when_ids_exist(
    repository: PgDocumentRepository,
    session: AsyncSession,
) -> None:
    doc1 = Document.create(
        source="https://example.com/a",
        title="Doc A",
        source_type=SourceType.URL,
    )
    doc2 = Document.create(
        source="https://example.com/b",
        title="Doc B",
        source_type=SourceType.URL,
    )

    await repository.save(doc1)
    await repository.save(doc2)
    await session.commit()

    result = await repository.find_by_ids({doc1.id, doc2.id, "nonexistent-id"})

    assert len(result) == 2
    assert result[doc1.id].title == "Doc A"
    assert result[doc2.id].title == "Doc B"
    assert "nonexistent-id" not in result


@pytest.mark.asyncio
async def test_find_by_ids_should_return_empty_dict_when_ids_empty(
    repository: PgDocumentRepository,
) -> None:
    result = await repository.find_by_ids(set())
    assert result == {}


@pytest.mark.asyncio
async def test_list_all_should_return_all_saved_documents(
    repository: PgDocumentRepository,
    session: AsyncSession,
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
    await session.commit()

    documents = await repository.list_all()
    ids = {d.id for d in documents}
    assert doc1.id in ids
    assert doc2.id in ids
