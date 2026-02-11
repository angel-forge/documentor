from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class AskQuestionRequest(BaseModel):
    question: str


class IngestDocumentRequest(BaseModel):
    source: str
    on_duplicate: Literal["reject", "skip", "replace"] = "reject"


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
