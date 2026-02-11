from abc import ABC, abstractmethod

from documentor.domain.models.chunk import Embedding


class EmbeddingService(ABC):
    @abstractmethod
    async def embed(self, text: str) -> Embedding: ...

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[Embedding]: ...

    @abstractmethod
    def count_tokens(self, text: str) -> int: ...
