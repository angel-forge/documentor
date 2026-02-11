from unittest.mock import AsyncMock

import pytest

from documentor.application.dtos import IngestDocumentationInput
from documentor.application.use_cases.ingest_documentation import IngestDocumentation
from documentor.domain.models.chunk import Embedding
from documentor.domain.models.document import SourceType
from documentor.domain.services.document_loader_service import LoadedDocument
from documentor.infrastructure.persistence.pg_unit_of_work import PgUnitOfWork


@pytest.mark.asyncio
async def test_ingest_should_save_document_and_chunks_when_using_real_db(
    session_factory,
) -> None:
    loader = AsyncMock()
    loader.load.return_value = LoadedDocument(
        content="word " * 100,
        title="Test Doc",
        source_type=SourceType.URL,
    )

    embedding = Embedding.from_list([0.1] * 1536)
    embedding_service = AsyncMock()
    embedding_service.embed_batch.return_value = [embedding]

    uow = PgUnitOfWork(session_factory)

    use_case = IngestDocumentation(
        loader=loader,
        embedding_service=embedding_service,
        uow=uow,
    )

    result = await use_case.execute(
        IngestDocumentationInput(source="https://example.com")
    )

    assert result.document.title == "Test Doc"
    assert result.chunks_created == 1

    # Verify data persisted by reading with a fresh UoW
    async with PgUnitOfWork(session_factory) as read_uow:
        saved_doc = await read_uow.documents.find_by_id(result.document.id)
        assert saved_doc is not None
        assert saved_doc.title == "Test Doc"
