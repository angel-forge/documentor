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


# ─── Hybrid search integration tests ─────────────────────────────────────────


@pytest.fixture
def hybrid_repository(session: AsyncSession) -> PgChunkRepository:
    return PgChunkRepository(session, search_language="english", rrf_k=60)


@pytest.mark.asyncio
async def test_search_hybrid_should_return_results_combining_vector_and_fts_when_both_match(
    hybrid_repository: PgChunkRepository,
    document: Document,
    session: AsyncSession,
) -> None:
    chunks = [
        Chunk(
            id="chunk-asyncsession",
            document_id=document.id,
            content=ChunkContent(
                text="Use AsyncSession for async database operations", token_count=8
            ),
            position=0,
            embedding=_make_embedding(0.8),
        ),
        Chunk(
            id="chunk-other",
            document_id=document.id,
            content=ChunkContent(text="Unrelated topic about logging", token_count=5),
            position=1,
            embedding=_make_embedding(0.2),
        ),
    ]
    await hybrid_repository.save_all(chunks)
    await session.commit()

    query_embedding = _make_embedding(0.9)
    results = await hybrid_repository.search_hybrid(
        query_embedding, "AsyncSession database", top_k=2
    )

    assert len(results) > 0
    ids = [chunk.id for chunk, _ in results]
    assert "chunk-asyncsession" in ids
    for _, score in results:
        assert 0.0 <= score <= 1.0


@pytest.mark.asyncio
async def test_search_hybrid_should_return_vector_only_results_when_no_fts_match(
    hybrid_repository: PgChunkRepository,
    document: Document,
    session: AsyncSession,
) -> None:
    chunks = [
        Chunk(
            id="chunk-vec-1",
            document_id=document.id,
            content=ChunkContent(text="Python async programming patterns", token_count=5),
            position=0,
            embedding=_make_embedding(0.9),
        ),
        Chunk(
            id="chunk-vec-2",
            document_id=document.id,
            content=ChunkContent(text="Database connection management", token_count=5),
            position=1,
            embedding=_make_embedding(0.5),
        ),
    ]
    await hybrid_repository.save_all(chunks)
    await session.commit()

    query_embedding = _make_embedding(1.0)
    # "xyzzy42" is a nonsense token that won't match any tsvector
    results = await hybrid_repository.search_hybrid(
        query_embedding, "xyzzy42nonexistent", top_k=2
    )

    # Vector results should still be returned even though FTS returns nothing
    assert len(results) > 0
    ids = {chunk.id for chunk, _ in results}
    assert "chunk-vec-1" in ids


@pytest.mark.asyncio
async def test_search_hybrid_should_handle_stop_words_only_query_when_fts_empty(
    hybrid_repository: PgChunkRepository,
    document: Document,
    session: AsyncSession,
) -> None:
    chunks = [
        Chunk(
            id="chunk-stopwords",
            document_id=document.id,
            content=ChunkContent(text="The quick brown fox jumps", token_count=6),
            position=0,
            embedding=_make_embedding(0.8),
        ),
    ]
    await hybrid_repository.save_all(chunks)
    await session.commit()

    query_embedding = _make_embedding(0.9)
    # "the a is" are all English stop words — plainto_tsquery returns empty query
    results = await hybrid_repository.search_hybrid(
        query_embedding, "the a is", top_k=5
    )

    # Should not raise; should return vector-only results
    assert isinstance(results, list)
    # The chunk can appear via vector search
    if results:
        for _, score in results:
            assert 0.0 <= score <= 1.0


@pytest.mark.asyncio
async def test_search_hybrid_should_boost_exact_keyword_matches_when_text_matches_query(
    hybrid_repository: PgChunkRepository,
    document: Document,
    session: AsyncSession,
) -> None:
    # chunk-keyword: exact match for "AsyncSession", moderate vector similarity
    # chunk-semantic: high vector similarity, no keyword match
    chunks = [
        Chunk(
            id="chunk-keyword",
            document_id=document.id,
            content=ChunkContent(
                text="Use AsyncSession to open a database connection", token_count=9
            ),
            position=0,
            embedding=_make_embedding(0.5),  # moderate vector similarity
        ),
        Chunk(
            id="chunk-semantic",
            document_id=document.id,
            content=ChunkContent(
                text="Open a session to connect to the database backend", token_count=10
            ),
            position=1,
            embedding=_make_embedding(0.95),  # high vector similarity
        ),
    ]
    await hybrid_repository.save_all(chunks)
    await session.commit()

    # Query embedding close to chunk-semantic, but text query targets AsyncSession
    query_embedding = _make_embedding(1.0)
    results = await hybrid_repository.search_hybrid(
        query_embedding, "AsyncSession", top_k=2
    )

    assert len(results) == 2
    scores_by_id = {chunk.id: score for chunk, score in results}
    # chunk-keyword should have higher RRF score because it appears in FTS results
    # while chunk-semantic only appears in vector results
    assert scores_by_id["chunk-keyword"] > scores_by_id["chunk-semantic"]


@pytest.mark.asyncio
async def test_search_hybrid_should_respect_top_k_when_many_candidates(
    hybrid_repository: PgChunkRepository,
    document: Document,
    session: AsyncSession,
) -> None:
    chunks = [
        Chunk(
            id=f"chunk-many-{i}",
            document_id=document.id,
            content=ChunkContent(
                text=f"Python programming tutorial number {i}", token_count=6
            ),
            position=i,
            embedding=_make_embedding(float(i) / 10),
        )
        for i in range(8)
    ]
    await hybrid_repository.save_all(chunks)
    await session.commit()

    query_embedding = _make_embedding(1.0)
    results = await hybrid_repository.search_hybrid(
        query_embedding, "Python programming", top_k=3
    )

    assert len(results) <= 3


@pytest.mark.asyncio
async def test_search_hybrid_should_return_empty_when_no_chunks_exist(
    hybrid_repository: PgChunkRepository,
) -> None:
    query_embedding = _make_embedding(1.0)
    results = await hybrid_repository.search_hybrid(
        query_embedding, "anything", top_k=5
    )

    assert results == []


@pytest.mark.asyncio
async def test_search_hybrid_should_return_normalized_scores_in_unit_interval(
    hybrid_repository: PgChunkRepository,
    document: Document,
    session: AsyncSession,
) -> None:
    chunks = [
        Chunk(
            id="chunk-norm",
            document_id=document.id,
            content=ChunkContent(
                text="SQLAlchemy ORM session management patterns", token_count=7
            ),
            position=0,
            embedding=_make_embedding(0.9),
        ),
    ]
    await hybrid_repository.save_all(chunks)
    await session.commit()

    query_embedding = _make_embedding(1.0)
    results = await hybrid_repository.search_hybrid(
        query_embedding, "SQLAlchemy session", top_k=5
    )

    assert len(results) > 0
    for _, score in results:
        assert 0.0 <= score <= 1.0, f"Score {score} out of [0, 1] range"


@pytest.mark.asyncio
async def test_search_hybrid_should_not_regress_search_similar_when_called_directly(
    hybrid_repository: PgChunkRepository,
    document: Document,
    session: AsyncSession,
) -> None:
    """SC-13: search_similar must remain functional after hybrid search is added."""
    chunks = [
        Chunk(
            id="chunk-compat-close",
            document_id=document.id,
            content=ChunkContent(text="Close chunk for compatibility test", token_count=6),
            position=0,
            embedding=_make_embedding(0.9),
        ),
        Chunk(
            id="chunk-compat-far",
            document_id=document.id,
            content=ChunkContent(text="Far chunk for compatibility test", token_count=6),
            position=1,
            embedding=_make_embedding(0.1),
        ),
    ]
    await hybrid_repository.save_all(chunks)
    await session.commit()

    query_embedding = _make_embedding(1.0)
    results = await hybrid_repository.search_similar(query_embedding, top_k=2)

    assert len(results) == 2
    assert results[0][0].id == "chunk-compat-close"
    assert results[1][0].id == "chunk-compat-far"
    for _, score in results:
        assert 0.0 <= score <= 1.0


# ─── Multi-language FTS integration tests ─────────────────────────────────────
# These tests require the trigger to exist. The trigger is created in the
# `session_with_trigger` fixture below because create_all only creates ORM
# table structures, not PostgreSQL triggers.


@pytest_asyncio.fixture
async def session_with_trigger(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncSession:
    """Session for trigger-dependent tests.

    The trigger is already installed at session_factory level (via conftest.py).
    This fixture is a plain session alias kept for semantic clarity.
    """
    session = session_factory()
    yield session
    await session.close()


@pytest_asyncio.fixture
async def document_for_trigger(session_with_trigger: AsyncSession) -> Document:
    repo = PgDocumentRepository(session_with_trigger)
    doc = Document.create(
        source="https://trigger-test.example.com/docs",
        title="Trigger Test Doc",
        source_type=SourceType.URL,
        chunk_count=2,
    )
    await repo.save(doc)
    await session_with_trigger.commit()
    return doc


@pytest.mark.asyncio
async def test_save_all_should_populate_search_vector_via_trigger_when_language_is_spanish(
    session_with_trigger: AsyncSession,
    document_for_trigger: Document,
) -> None:
    """SC-11: trigger fires on INSERT and populates search_vector with correct language."""
    from sqlalchemy import text as sa_text

    repo = PgChunkRepository(session_with_trigger)
    chunks = [
        Chunk(
            id="chunk-es-1",
            document_id=document_for_trigger.id,
            content=ChunkContent(text="La programación asíncrona es fundamental", token_count=6),
            position=0,
            language="spanish",
        ),
    ]
    await repo.save_all(chunks)
    await session_with_trigger.commit()

    result = await session_with_trigger.execute(
        sa_text("SELECT search_vector IS NOT NULL FROM chunks WHERE id = 'chunk-es-1'")
    )
    is_populated = result.scalar()
    assert is_populated is True


@pytest.mark.asyncio
async def test_fts_search_should_find_spanish_chunks_when_queried_in_spanish(
    session_with_trigger: AsyncSession,
    document_for_trigger: Document,
) -> None:
    """SC-08 variant: FTS with correct language finds stemmed terms."""
    repo = PgChunkRepository(session_with_trigger, search_language="spanish")
    chunks = [
        Chunk(
            id="chunk-es-fts-1",
            document_id=document_for_trigger.id,
            content=ChunkContent(
                text="La programación asíncrona es fundamental para el rendimiento",
                token_count=10,
            ),
            position=0,
            embedding=_make_embedding(0.5),
            language="spanish",
        ),
    ]
    await repo.save_all(chunks)
    await session_with_trigger.commit()

    results = await repo._fts_search("programación", "spanish", 5)

    assert len(results) > 0
    ids = [r[0] for r in results]
    assert "chunk-es-fts-1" in ids


@pytest.mark.asyncio
async def test_search_similar_should_be_unaffected_by_language_field(
    session_with_trigger: AsyncSession,
    document_for_trigger: Document,
) -> None:
    """SC-15: search_similar works identically regardless of chunk language."""
    repo = PgChunkRepository(session_with_trigger)
    chunks = [
        Chunk(
            id="chunk-ml-close",
            document_id=document_for_trigger.id,
            content=ChunkContent(text="Close multilang chunk", token_count=3),
            position=0,
            embedding=_make_embedding(0.9),
            language="spanish",
        ),
        Chunk(
            id="chunk-ml-far",
            document_id=document_for_trigger.id,
            content=ChunkContent(text="Far multilang chunk", token_count=3),
            position=1,
            embedding=_make_embedding(0.1),
            language="french",
        ),
    ]
    await repo.save_all(chunks)
    await session_with_trigger.commit()

    query_embedding = _make_embedding(1.0)
    results = await repo.search_similar(query_embedding, top_k=2)

    assert len(results) == 2
    ids = [chunk.id for chunk, _ in results]
    assert "chunk-ml-close" in ids
    assert "chunk-ml-far" in ids
    for _, score in results:
        assert 0.0 <= score <= 1.0
