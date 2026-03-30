"""Unit tests for _to_model / _to_entity mapper functions in pg repositories.

These functions are pure (no I/O) so they can be tested without a database.
"""

from datetime import UTC, datetime

from documentor.domain.models.chunk import Chunk, ChunkContent
from documentor.domain.models.document import Document, SourceType
from documentor.infrastructure.persistence.orm_models import ChunkModel, DocumentModel
from documentor.infrastructure.persistence.pg_chunk_repository import (
    _to_entity as chunk_to_entity,
    _to_model as chunk_to_model,
)
from documentor.infrastructure.persistence.pg_document_repository import (
    _to_entity as document_to_entity,
    _to_model as document_to_model,
)


class TestChunkMappers:
    def test_to_model_chunk_should_include_language_when_chunk_has_language(
        self,
    ) -> None:
        chunk = Chunk(
            id="chunk-1",
            document_id="doc-1",
            content=ChunkContent(text="Bonjour le monde", token_count=3),
            position=0,
            language="french",
        )

        model = chunk_to_model(chunk)

        assert model.language == "french"

    def test_to_entity_chunk_should_preserve_language_when_model_has_language(
        self,
    ) -> None:
        model = ChunkModel(
            id="chunk-1",
            document_id="doc-1",
            text="Hola mundo",
            token_count=2,
            position=0,
            embedding=None,
            language="spanish",
        )

        chunk = chunk_to_entity(model)

        assert chunk.language == "spanish"

    def test_to_model_chunk_should_default_language_to_english_when_not_set(
        self,
    ) -> None:
        chunk = Chunk(
            id="chunk-2",
            document_id="doc-1",
            content=ChunkContent(text="Hello world", token_count=2),
            position=0,
        )

        model = chunk_to_model(chunk)

        assert model.language == "english"


class TestDocumentMappers:
    def _make_doc(self, language: str = "german") -> Document:
        return Document(
            id="doc-1",
            source="https://example.com/docs",
            title="Docs",
            source_type=SourceType.URL,
            created_at=datetime(2024, 1, 1, tzinfo=UTC),
            chunk_count=0,
            language=language,
        )

    def test_to_model_document_should_include_language(self) -> None:
        doc = self._make_doc(language="german")

        model = document_to_model(doc)

        assert model.language == "german"

    def test_to_entity_document_should_preserve_language(self) -> None:
        model = DocumentModel(
            id="doc-1",
            source="https://example.com/docs",
            title="Docs",
            source_type="url",
            created_at=datetime(2024, 1, 1, tzinfo=UTC),
            chunk_count=0,
            language="portuguese",
        )

        doc = document_to_entity(model)

        assert doc.language == "portuguese"
