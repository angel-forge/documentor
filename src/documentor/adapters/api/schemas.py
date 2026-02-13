from datetime import datetime
from typing import Literal
from urllib.parse import urlparse

from pydantic import BaseModel, field_validator


class AskQuestionRequest(BaseModel):
    question: str


class IngestDocumentRequest(BaseModel):
    source: str
    on_duplicate: Literal["reject", "skip", "replace"] = "reject"

    @field_validator("source")
    @classmethod
    def source_must_be_http_url(cls, v: str) -> str:
        parsed = urlparse(v)
        if parsed.scheme not in ("http", "https"):
            raise ValueError("Source must be an HTTP or HTTPS URL")
        if not parsed.netloc:
            raise ValueError("Source must include a valid hostname")
        return v


class SourceReferenceResponse(BaseModel):
    document_title: str
    chunk_text: str
    relevance_score: float
    chunk_id: str


class AnswerResponse(BaseModel):
    text: str
    sources: list[SourceReferenceResponse]


class DocumentResponse(BaseModel):
    id: str
    source: str
    title: str
    source_type: str
    created_at: datetime
    chunk_count: int


class IngestDocumentResponse(BaseModel):
    document: DocumentResponse
    chunks_created: int


class HealthResponse(BaseModel):
    status: str
