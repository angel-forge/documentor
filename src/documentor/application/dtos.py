from dataclasses import dataclass
from datetime import datetime

from documentor.domain.models.answer import Answer, SourceReference
from documentor.domain.models.document import Document


@dataclass(frozen=True)
class IngestDocumentationInput:
    source: str
    on_duplicate: str = "reject"


@dataclass(frozen=True)
class AskQuestionInput:
    question_text: str


@dataclass(frozen=True)
class SourceReferenceDTO:
    document_title: str
    chunk_text: str
    relevance_score: float
    chunk_id: str

    @staticmethod
    def from_domain(source: SourceReference) -> "SourceReferenceDTO":
        return SourceReferenceDTO(
            document_title=source.document_title,
            chunk_text=source.chunk_text,
            relevance_score=source.relevance_score,
            chunk_id=source.chunk_id,
        )


@dataclass(frozen=True)
class AnswerDTO:
    text: str
    sources: list[SourceReferenceDTO]

    @staticmethod
    def from_domain(answer: Answer) -> "AnswerDTO":
        return AnswerDTO(
            text=answer.text,
            sources=[SourceReferenceDTO.from_domain(s) for s in answer.sources],
        )


@dataclass(frozen=True)
class DocumentDTO:
    id: str
    source: str
    title: str
    source_type: str
    created_at: datetime
    chunk_count: int

    @staticmethod
    def from_entity(document: Document) -> "DocumentDTO":
        return DocumentDTO(
            id=document.id,
            source=document.source,
            title=document.title,
            source_type=str(document.source_type),
            created_at=document.created_at,
            chunk_count=document.chunk_count,
        )


@dataclass(frozen=True)
class IngestResultDTO:
    document: DocumentDTO
    chunks_created: int
