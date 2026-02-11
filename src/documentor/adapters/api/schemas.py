from datetime import datetime

from pydantic import BaseModel


class AskQuestionRequest(BaseModel):
    question: str


class IngestDocumentRequest(BaseModel):
    source: str


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
