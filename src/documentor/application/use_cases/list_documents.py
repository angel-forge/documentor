from documentor.domain.unit_of_work import UnitOfWork

from documentor.application.dtos import DocumentDTO


class ListDocuments:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def execute(self) -> list[DocumentDTO]:
        """List all ingested documents."""
        async with self._uow:
            documents = await self._uow.documents.list_all()
        return [DocumentDTO.from_entity(doc) for doc in documents]
