from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from documentor.domain.models.document import Document, SourceType
from documentor.domain.repositories.document_repository import DocumentRepository
from documentor.infrastructure.persistence.orm_models import DocumentModel


class PgDocumentRepository(DocumentRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def save(self, document: Document) -> Document:
        async with self._session_factory() as session:
            model = _to_model(document)
            session.add(model)
            await session.commit()
            return document

    async def find_by_id(self, document_id: str) -> Document | None:
        async with self._session_factory() as session:
            model = await session.get(DocumentModel, document_id)
            if model is None:
                return None
            return _to_entity(model)

    async def list_all(self) -> list[Document]:
        async with self._session_factory() as session:
            result = await session.execute(select(DocumentModel))
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
