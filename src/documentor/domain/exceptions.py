class DocumentorDomainError(Exception):
    """Base exception for all domain errors."""


class DocumentNotFoundError(DocumentorDomainError):
    def __init__(self, document_id: str) -> None:
        self.document_id = document_id
        super().__init__(f"Document not found: {document_id}")


class InvalidDocumentError(DocumentorDomainError):
    pass


class InvalidChunkError(DocumentorDomainError):
    pass


class InvalidQuestionError(DocumentorDomainError):
    pass


class InvalidEmbeddingError(DocumentorDomainError):
    pass


class DocumentLoadError(DocumentorDomainError):
    pass


class EmbeddingGenerationError(DocumentorDomainError):
    pass


class LLMGenerationError(DocumentorDomainError):
    pass
