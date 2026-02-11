from documentor.domain.repositories.document_repository import DocumentRepository

from documentor.application.dtos import DocumentDTO


class ListDocuments:
    def __init__(self, document_repository: DocumentRepository) -> None:
        self._document_repository = document_repository

    async def execute(self) -> list[DocumentDTO]:
        """List all ingested documents."""
        documents = await self._document_repository.list_all()
        return [DocumentDTO.from_entity(doc) for doc in documents]
