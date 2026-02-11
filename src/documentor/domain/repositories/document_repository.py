from abc import ABC, abstractmethod

from documentor.domain.models.document import Document


class DocumentRepository(ABC):
    @abstractmethod
    async def save(self, document: Document) -> Document: ...

    @abstractmethod
    async def find_by_id(self, document_id: str) -> Document | None: ...

    @abstractmethod
    async def find_by_ids(self, document_ids: set[str]) -> dict[str, Document]: ...

    @abstractmethod
    async def find_by_source(self, source: str) -> Document | None: ...

    @abstractmethod
    async def delete(self, document_id: str) -> None: ...

    @abstractmethod
    async def list_all(self) -> list[Document]: ...
