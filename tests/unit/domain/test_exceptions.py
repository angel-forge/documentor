from documentor.domain.exceptions import (
    DocumentLoadError,
    DocumentNotFoundError,
    DocumentorDomainError,
    EmbeddingGenerationError,
    InvalidChunkError,
    InvalidDocumentError,
    InvalidEmbeddingError,
    InvalidQuestionError,
    LLMGenerationError,
)


class TestDomainExceptions:
    def test_domain_exceptions_should_inherit_from_base_when_checked(self) -> None:
        exceptions = [
            DocumentNotFoundError("123"),
            InvalidDocumentError(),
            InvalidChunkError(),
            InvalidQuestionError(),
            InvalidEmbeddingError(),
            DocumentLoadError(),
            EmbeddingGenerationError(),
            LLMGenerationError(),
        ]
        for exc in exceptions:
            assert isinstance(exc, DocumentorDomainError)

    def test_document_not_found_should_store_id_when_raised(self) -> None:
        exc = DocumentNotFoundError("abc-123")
        assert exc.document_id == "abc-123"
        assert "abc-123" in str(exc)
