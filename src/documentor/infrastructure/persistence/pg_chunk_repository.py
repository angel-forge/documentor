from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from documentor.domain.models.chunk import Chunk, ChunkContent, Embedding
from documentor.domain.repositories.chunk_repository import ChunkRepository
from documentor.infrastructure.persistence.orm_models import ChunkModel


class PgChunkRepository(ChunkRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

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
