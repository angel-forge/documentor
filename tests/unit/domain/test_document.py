import pytest

from documentor.domain.exceptions import InvalidDocumentError
from documentor.domain.models.document import Document, SourceType


class TestDocument:
    def test_create_document_should_generate_id_and_timestamp_when_using_factory(
        self,
    ) -> None:
        doc = Document.create(
            source="https://docs.example.com",
            title="Example Docs",
            source_type=SourceType.URL,
        )
        assert doc.id
        assert doc.created_at is not None
        assert doc.created_at.tzinfo is not None
        assert doc.chunk_count == 0
        assert doc.source == "https://docs.example.com"
        assert doc.title == "Example Docs"
        assert doc.source_type == SourceType.URL

    def test_create_document_should_raise_error_when_source_is_empty(self) -> None:
        with pytest.raises(InvalidDocumentError, match="source"):
            Document.create(
                source="",
                title="Title",
                source_type=SourceType.URL,
            )

    def test_create_document_should_raise_error_when_title_is_empty(self) -> None:
        with pytest.raises(InvalidDocumentError, match="title"):
            Document.create(
                source="https://example.com",
                title="   ",
                source_type=SourceType.URL,
            )
