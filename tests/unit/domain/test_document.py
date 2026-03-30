import pytest

from documentor.domain.exceptions import InvalidDocumentError
from documentor.domain.models.document import (
    SUPPORTED_FTS_LANGUAGES,
    Document,
    SourceType,
)


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

    def test_create_should_set_language_when_provided(self) -> None:
        doc = Document.create(
            source="https://docs.example.com",
            title="Docs",
            source_type=SourceType.URL,
            language="spanish",
        )
        assert doc.language == "spanish"

    def test_create_should_default_language_to_english_when_not_provided(self) -> None:
        doc = Document.create(
            source="https://docs.example.com",
            title="Docs",
            source_type=SourceType.URL,
        )
        assert doc.language == "english"

    def test_init_should_raise_when_language_unsupported(self) -> None:
        with pytest.raises(InvalidDocumentError, match="klingon"):
            Document.create(
                source="https://docs.example.com",
                title="Docs",
                source_type=SourceType.URL,
                language="klingon",
            )

    @pytest.mark.parametrize("language", sorted(SUPPORTED_FTS_LANGUAGES))
    def test_init_should_accept_all_supported_languages(self, language: str) -> None:
        doc = Document.create(
            source="https://docs.example.com",
            title="Docs",
            source_type=SourceType.URL,
            language=language,
        )
        assert doc.language == language
