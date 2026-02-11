from abc import ABC, abstractmethod

from documentor.domain.models.chunk import Chunk, Embedding


class ChunkRepository(ABC):
    @abstractmethod
    async def save_all(self, chunks: list[Chunk]) -> list[Chunk]: ...

    @abstractmethod
    async def search_similar(
        self, embedding: Embedding, top_k: int = 5
    ) -> list[tuple[Chunk, float]]: ...

    @abstractmethod
    async def delete_by_document_id(self, document_id: str) -> None: ...
