from sqlalchemy import String, cast, delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from documentor.domain.models.chunk import Chunk, ChunkContent, Embedding
from documentor.domain.repositories.chunk_repository import ChunkRepository
from documentor.infrastructure.persistence.orm_models import ChunkModel


def reciprocal_rank_fusion(
    ranked_lists: list[list[tuple[str, Chunk, float]]],
    top_k: int,
    k: int = 60,
) -> list[tuple[Chunk, float]]:
    """Merge multiple ranked lists using Reciprocal Rank Fusion.

    Each ranked list contains tuples of (chunk_id, Chunk, original_score).
    Items are identified by chunk_id for deduplication.
    Returns top_k results with normalized RRF scores in [0, 1].

    Normalization: score / (num_lists / (k + 1)) so that a chunk ranked
    #1 in all lists receives a normalized score of 1.0.
    """
    num_lists = len(ranked_lists)
    if num_lists == 0:
        return []

    max_score = num_lists / (k + 1)

    scores: dict[str, float] = {}
    chunks: dict[str, Chunk] = {}

    for ranked_list in ranked_lists:
        for rank, (chunk_id, chunk, _original_score) in enumerate(ranked_list, start=1):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (k + rank)
            chunks[chunk_id] = chunk

    normalized: list[tuple[Chunk, float]] = [
        (chunks[cid], score / max_score) for cid, score in scores.items()
    ]
    normalized.sort(key=lambda x: x[1], reverse=True)
    return normalized[:top_k]


class PgChunkRepository(ChunkRepository):
    def __init__(
        self,
        session: AsyncSession,
        search_language: str = "english",
        rrf_k: int = 60,
    ) -> None:
        self._session = session
        self._search_language = search_language
        self._rrf_k = rrf_k

    async def save_all(self, chunks: list[Chunk]) -> list[Chunk]:
        models = [_to_model(chunk) for chunk in chunks]
        self._session.add_all(models)
        await self._session.flush()
        return chunks

    async def search_similar(
        self, embedding: Embedding, top_k: int = 5
    ) -> list[tuple[Chunk, float]]:
        vector = list(embedding.vector)
        distance_expr = ChunkModel.embedding.cosine_distance(vector)
        stmt = (
            select(ChunkModel, distance_expr.label("distance"))
            .where(ChunkModel.embedding.isnot(None))
            .order_by(distance_expr)
            .limit(top_k)
        )
        result = await self._session.execute(stmt)
        rows = result.all()
        return [(_to_entity(row[0]), 1.0 - float(row[1])) for row in rows]

    async def search_hybrid(
        self,
        embedding: Embedding,
        query_text: str,
        top_k: int = 5,
        language: str = "english",
    ) -> list[tuple[Chunk, float]]:
        """Combine vector search and full-text search via Reciprocal Rank Fusion."""
        candidate_count = top_k * 2
        vector_results = await self._vector_search(embedding, candidate_count)
        fts_results = await self._fts_search(query_text, language, candidate_count)
        return reciprocal_rank_fusion(
            ranked_lists=[vector_results, fts_results],
            top_k=top_k,
            k=self._rrf_k,
        )

    async def _vector_search(
        self,
        embedding: Embedding,
        candidate_count: int,
    ) -> list[tuple[str, Chunk, float]]:
        """Run cosine-similarity vector search; returns (chunk_id, chunk, score)."""
        vector = list(embedding.vector)
        distance_expr = ChunkModel.embedding.cosine_distance(vector)
        stmt = (
            select(ChunkModel, distance_expr.label("distance"))
            .where(ChunkModel.embedding.isnot(None))
            .order_by(distance_expr)
            .limit(candidate_count)
        )
        result = await self._session.execute(stmt)
        rows = result.all()
        return [(row[0].id, _to_entity(row[0]), 1.0 - float(row[1])) for row in rows]

    async def _fts_search(
        self,
        query_text: str,
        language: str,
        candidate_count: int,
    ) -> list[tuple[str, Chunk, float]]:
        """Run full-text search using plainto_tsquery + ts_rank_cd.

        Returns empty list if query_text is empty or produces an empty tsquery
        (e.g., all stop words).
        """
        if not query_text.strip():
            return []

        tsquery = func.plainto_tsquery(language, query_text)

        # Check if tsquery is empty by casting it to text and comparing.
        # plainto_tsquery('english', 'the a is') returns an empty tsquery object.
        empty_check = await self._session.execute(
            select(cast(tsquery, String).label("q"))
        )
        tsquery_text = empty_check.scalar()
        if not tsquery_text:
            return []

        rank_expr = func.ts_rank_cd(ChunkModel.search_vector, tsquery).label("rank_score")
        stmt = (
            select(ChunkModel, rank_expr)
            .where(ChunkModel.search_vector.op("@@")(tsquery))
            .order_by(rank_expr.desc())
            .limit(candidate_count)
        )
        result = await self._session.execute(stmt)
        rows = result.all()
        return [(row[0].id, _to_entity(row[0]), float(row[1])) for row in rows]

    async def delete_by_document_id(self, document_id: str) -> None:
        stmt = delete(ChunkModel).where(ChunkModel.document_id == document_id)
        await self._session.execute(stmt)
        await self._session.flush()


def _to_model(chunk: Chunk) -> ChunkModel:
    return ChunkModel(
        id=chunk.id,
        document_id=chunk.document_id,
        text=chunk.content.text,
        token_count=chunk.content.token_count,
        position=chunk.position,
        embedding=list(chunk.embedding.vector) if chunk.embedding else None,
    )


def _to_entity(model: ChunkModel) -> Chunk:
    embedding = None
    if model.embedding is not None:
        embedding = Embedding.from_list(list(model.embedding))
    return Chunk(
        id=model.id,
        document_id=model.document_id,
        content=ChunkContent(text=model.text, token_count=model.token_count),
        position=model.position,
        embedding=embedding,
    )
