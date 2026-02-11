from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from documentor.domain.models.document import Document, SourceType
from documentor.domain.repositories.document_repository import DocumentRepository
from documentor.infrastructure.persistence.orm_models import DocumentModel


class PgDocumentRepository(DocumentRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, document: Document) -> Document:
        model = _to_model(document)
        self._session.add(model)
        await self._session.flush()
        return document

    async def find_by_id(self, document_id: str) -> Document | None:
        model = await self._session.get(DocumentModel, document_id)
        if model is None:
            return None
        return _to_entity(model)

    async def find_by_ids(self, document_ids: set[str]) -> dict[str, Document]:
        if not document_ids:
            return {}
        stmt = select(DocumentModel).where(DocumentModel.id.in_(document_ids))
        result = await self._session.execute(stmt)
        return {model.id: _to_entity(model) for model in result.scalars().all()}

    async def list_all(self) -> list[Document]:
        result = await self._session.execute(select(DocumentModel))
        return [_to_entity(model) for model in result.scalars().all()]


def _to_model(document: Document) -> DocumentModel:
    return DocumentModel(
        id=document.id,
        source=document.source,
        title=document.title,
        source_type=document.source_type.value,
        created_at=document.created_at,
        chunk_count=document.chunk_count,
    )


def _to_entity(model: DocumentModel) -> Document:
    return Document(
        id=model.id,
        source=model.source,
        title=model.title,
        source_type=SourceType(model.source_type),
        created_at=model.created_at,
        chunk_count=model.chunk_count,
    )
