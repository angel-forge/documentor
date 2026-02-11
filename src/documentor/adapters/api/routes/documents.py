from typing import Annotated

from fastapi import APIRouter, Depends

from documentor.adapters.api.dependencies import (
    get_ingest_documentation,
    get_list_documents,
)
from documentor.adapters.api.schemas import (
    DocumentResponse,
    IngestDocumentRequest,
    IngestDocumentResponse,
)
from documentor.application.dtos import IngestDocumentationInput
from documentor.application.use_cases.ingest_documentation import IngestDocumentation
from documentor.application.use_cases.list_documents import ListDocuments

router = APIRouter()


@router.post("/ingest/url", response_model=IngestDocumentResponse)
async def ingest_document(
    request: IngestDocumentRequest,
    use_case: Annotated[IngestDocumentation, Depends(get_ingest_documentation)],
) -> IngestDocumentResponse:
    """Ingest documentation from a URL."""
    result = await use_case.execute(
        IngestDocumentationInput(
            source=request.source,
            on_duplicate=request.on_duplicate,
        )
    )
    doc = result.document
    return IngestDocumentResponse(
        document=DocumentResponse(
            id=doc.id,
            source=doc.source,
            title=doc.title,
            source_type=doc.source_type,
            created_at=doc.created_at,
            chunk_count=doc.chunk_count,
        ),
        chunks_created=result.chunks_created,
    )


@router.get("/documents", response_model=list[DocumentResponse])
async def list_documents(
    use_case: Annotated[ListDocuments, Depends(get_list_documents)],
) -> list[DocumentResponse]:
    """List all ingested documents."""
    documents = await use_case.execute()
    return [
        DocumentResponse(
            id=doc.id,
            source=doc.source,
            title=doc.title,
            source_type=doc.source_type,
            created_at=doc.created_at,
            chunk_count=doc.chunk_count,
        )
        for doc in documents
    ]
