from datetime import datetime
from typing import Literal
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator

from documentor.domain.models.document import SUPPORTED_FTS_LANGUAGES


class ConversationMessageSchema(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1, max_length=10000)


class AskQuestionRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000)
    history: list[ConversationMessageSchema] = Field(default_factory=list, max_length=50)


class IngestDocumentRequest(BaseModel):
    source: str
    title: str | None = None
    on_duplicate: Literal["reject", "skip", "replace"] = "reject"
    language: str = "english"

    @field_validator("source")
    @classmethod
    def source_must_be_http_url(cls, v: str) -> str:
        parsed = urlparse(v)
        if parsed.scheme not in ("http", "https"):
            raise ValueError("Source must be an HTTP or HTTPS URL")
        if not parsed.netloc:
            raise ValueError("Source must include a valid hostname")
        return v

    @field_validator("language")
    @classmethod
    def language_must_be_supported(cls, v: str) -> str:
        normalized = v.lower()
        if normalized not in SUPPORTED_FTS_LANGUAGES:
            raise ValueError(
                f"Unsupported language: {v}. "
                f"Supported: {sorted(SUPPORTED_FTS_LANGUAGES)}"
            )
        return normalized


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
    language: str


class IngestDocumentResponse(BaseModel):
    document: DocumentResponse
    chunks_created: int


class HealthResponse(BaseModel):
    status: str
