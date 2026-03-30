import hashlib
from collections.abc import Callable
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from documentor.adapters.api.dependencies import (
    get_ingest_documentation,
    get_ingest_file_documentation,
    get_list_documents,
)
from documentor.adapters.api.file_validation import validate_upload_file
from documentor.adapters.api.schemas import (
    DocumentResponse,
    IngestDocumentRequest,
    IngestDocumentResponse,
)
from documentor.application.dtos import IngestDocumentationInput
from documentor.domain.models.document import SUPPORTED_FTS_LANGUAGES
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
            title=request.title,
            on_duplicate=request.on_duplicate,
            language=request.language,
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
            language=doc.language,
        ),
        chunks_created=result.chunks_created,
    )


@router.post("/ingest/file", response_model=IngestDocumentResponse)
async def ingest_file(
    file: Annotated[UploadFile, File()],
    use_case_factory: Annotated[
        Callable[[bytes, str], IngestDocumentation],
        Depends(get_ingest_file_documentation),
    ],
    title: Annotated[str | None, Form()] = None,
    on_duplicate: Annotated[Literal["reject", "skip", "replace"], Form()] = "reject",
    language: Annotated[str, Form()] = "english",
) -> IngestDocumentResponse:
    """Ingest documentation from an uploaded file."""
    content = await validate_upload_file(file)

    normalized_language = language.lower()
    if normalized_language not in SUPPORTED_FTS_LANGUAGES:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported language: {language}. Supported: {sorted(SUPPORTED_FTS_LANGUAGES)}",
        )

    source = f"sha256:{hashlib.sha256(content).hexdigest()}"
    use_case = use_case_factory(content, file.filename or "upload")

    result = await use_case.execute(
        IngestDocumentationInput(
            source=source,
            title=title,
            on_duplicate=on_duplicate,
            language=normalized_language,
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
            language=doc.language,
        ),
        chunks_created=result.chunks_created,
    )


@router.get("/documents", response_model=list[DocumentResponse])
async def list_documents(
    use_case: Annotated[ListDocuments, Depends(get_list_documents)],
    offset: int = 0,
    limit: int = 50,
) -> list[DocumentResponse]:
    """List ingested documents with pagination."""
    documents = await use_case.execute(offset=offset, limit=limit)
    return [
        DocumentResponse(
            id=doc.id,
            source=doc.source,
            title=doc.title,
            source_type=doc.source_type,
            created_at=doc.created_at,
            chunk_count=doc.chunk_count,
            language=doc.language,
        )
        for doc in documents
    ]
