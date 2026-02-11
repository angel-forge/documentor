from abc import ABC, abstractmethod
from types import TracebackType
from typing import Self

from documentor.domain.repositories.chunk_repository import ChunkRepository
from documentor.domain.repositories.document_repository import DocumentRepository


class UnitOfWork(ABC):
    documents: DocumentRepository
    chunks: ChunkRepository

    @abstractmethod
    async def commit(self) -> None: ...

    @abstractmethod
    async def rollback(self) -> None: ...

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if exc_type is not None:
            await self.rollback()
