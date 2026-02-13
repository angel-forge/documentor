from documentor.domain.unit_of_work import UnitOfWork

from documentor.application.dtos import DocumentDTO


class ListDocuments:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def execute(
        self, *, offset: int = 0, limit: int | None = None
    ) -> list[DocumentDTO]:
        """List ingested documents with optional pagination."""
        async with self._uow:
            documents = await self._uow.documents.list_all(
                offset=offset, limit=limit
            )
        return [DocumentDTO.from_entity(doc) for doc in documents]
