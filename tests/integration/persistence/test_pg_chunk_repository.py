import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from documentor.domain.models.chunk import Chunk, ChunkContent, Embedding
from documentor.domain.models.document import Document, SourceType
from documentor.infrastructure.persistence.pg_chunk_repository import (
    PgChunkRepository,
)
from documentor.infrastructure.persistence.pg_document_repository import (
    PgDocumentRepository,
)

DIMENSION = 1536


def _make_embedding(weight: float) -> Embedding:
    """Create a 1536-dim embedding that blends two orthogonal directions.

    weight=1.0 → mostly dimension 0, weight=0.0 → mostly dimension 1.
    This ensures different cosine angles between vectors.
    """
    vector = [0.0] * DIMENSION
    vector[0] = weight
    vector[1] = 1.0 - weight
    return Embedding(vector=tuple(vector), dimension=DIMENSION)


@pytest_asyncio.fixture
async def session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncSession:
    session = session_factory()
    yield session
    await session.close()


@pytest_asyncio.fixture
async def document(session: AsyncSession) -> Document:
    repo = PgDocumentRepository(session)
    doc = Document.create(
        source="https://example.com/test",
        title="Test Doc",
        source_type=SourceType.URL,
        chunk_count=3,
    )
    await repo.save(doc)
    await session.commit()
    return doc


@pytest.fixture
def repository(session: AsyncSession) -> PgChunkRepository:
    return PgChunkRepository(session)


@pytest.mark.asyncio
async def test_save_all_should_persist_chunks_with_embeddings(
    repository: PgChunkRepository,
    document: Document,
    session: AsyncSession,
) -> None:
    chunks = [
        Chunk(
            id=f"chunk-{i}",
            document_id=document.id,
            content=ChunkContent(text=f"Chunk text {i}", token_count=10),
            position=i,
            embedding=_make_embedding(float(i) / 10),
        )
        for i in range(3)
    ]

    saved = await repository.save_all(chunks)
    await session.commit()
    assert len(saved) == 3


@pytest.mark.asyncio
async def test_search_similar_should_return_closest_chunks_ordered(
    repository: PgChunkRepository,
    document: Document,
    session: AsyncSession,
) -> None:
    chunks = [
        Chunk(
            id="chunk-far",
            document_id=document.id,
            content=ChunkContent(text="Far chunk", token_count=5),
            position=0,
            embedding=_make_embedding(0.1),
        ),
        Chunk(
            id="chunk-close",
            document_id=document.id,
            content=ChunkContent(text="Close chunk", token_count=5),
            position=1,
            embedding=_make_embedding(0.9),
        ),
        Chunk(
            id="chunk-mid",
            document_id=document.id,
            content=ChunkContent(text="Mid chunk", token_count=5),
            position=2,
            embedding=_make_embedding(0.5),
        ),
    ]
    await repository.save_all(chunks)
    await session.commit()

    query_embedding = _make_embedding(1.0)
    results = await repository.search_similar(query_embedding, top_k=3)

    assert len(results) == 3
    # Closest first (0.9 is closest to 1.0)
    assert results[0][0].id == "chunk-close"
    assert results[1][0].id == "chunk-mid"
    assert results[2][0].id == "chunk-far"
    # Scores should be between 0 and 1
    for _, score in results:
        assert 0.0 <= score <= 1.0


@pytest.mark.asyncio
async def test_search_similar_should_respect_top_k(
    repository: PgChunkRepository,
    document: Document,
    session: AsyncSession,
) -> None:
    chunks = [
        Chunk(
            id=f"chunk-topk-{i}",
            document_id=document.id,
            content=ChunkContent(text=f"Chunk {i}", token_count=5),
            position=i,
            embedding=_make_embedding(float(i) / 10),
        )
        for i in range(5)
    ]
    await repository.save_all(chunks)
    await session.commit()

    query_embedding = _make_embedding(1.0)
    results = await repository.search_similar(query_embedding, top_k=2)

    assert len(results) == 2


@pytest.mark.asyncio
async def test_search_similar_should_return_empty_when_no_chunks(
    repository: PgChunkRepository,
) -> None:
    query_embedding = _make_embedding(1.0)
    results = await repository.search_similar(query_embedding, top_k=5)

    assert results == []
