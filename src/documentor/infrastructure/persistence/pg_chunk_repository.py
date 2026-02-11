from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from documentor.domain.models.chunk import Chunk, ChunkContent, Embedding
from documentor.domain.repositories.chunk_repository import ChunkRepository
from documentor.infrastructure.persistence.orm_models import ChunkModel


class PgChunkRepository(ChunkRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def save_all(self, chunks: list[Chunk]) -> list[Chunk]:
        async with self._session_factory() as session:
            models = [_to_model(chunk) for chunk in chunks]
            session.add_all(models)
            await session.commit()
            return chunks

    async def search_similar(
        self, embedding: Embedding, top_k: int = 5
    ) -> list[tuple[Chunk, float]]:
        vector = list(embedding.vector)
        async with self._session_factory() as session:
            distance_expr = ChunkModel.embedding.cosine_distance(vector)
            stmt = (
                select(ChunkModel, distance_expr.label("distance"))
                .where(ChunkModel.embedding.isnot(None))
                .order_by(distance_expr)
                .limit(top_k)
            )
            result = await session.execute(stmt)
            rows = result.all()
            return [(_to_entity(row[0]), 1.0 - float(row[1])) for row in rows]


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
