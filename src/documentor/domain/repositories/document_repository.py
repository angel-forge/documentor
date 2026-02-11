from abc import ABC, abstractmethod

from documentor.domain.models.document import Document


class DocumentRepository(ABC):
    @abstractmethod
    async def save(self, document: Document) -> Document: ...

    @abstractmethod
    async def find_by_id(self, document_id: str) -> Document | None: ...

    @abstractmethod
    async def list_all(self) -> list[Document]: ...
