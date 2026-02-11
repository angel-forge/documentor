import pytest

from documentor.domain.exceptions import InvalidChunkError, InvalidEmbeddingError
from documentor.domain.models.chunk import (
    Chunk,
    ChunkContent,
    Embedding,
    split_text_into_chunks,
)


class TestEmbedding:
    def test_embedding_should_raise_error_when_vector_length_mismatch(self) -> None:
        with pytest.raises(InvalidEmbeddingError, match="does not match"):
            Embedding(vector=(1.0, 2.0, 3.0), dimension=2)

    def test_embedding_from_list_should_create_embedding_when_valid_list(self) -> None:
        embedding = Embedding.from_list([0.1, 0.2, 0.3])
        assert embedding.dimension == 3
        assert embedding.vector == (0.1, 0.2, 0.3)


class TestChunkContent:
    def test_chunk_content_should_raise_error_when_text_is_empty(self) -> None:
        with pytest.raises(InvalidChunkError, match="text"):
            ChunkContent(text="", token_count=10)

    def test_chunk_content_should_raise_error_when_token_count_zero(self) -> None:
        with pytest.raises(InvalidChunkError, match="Token count"):
            ChunkContent(text="some text", token_count=0)


class TestChunk:
    def test_create_chunk_should_generate_id_when_using_factory(self) -> None:
        content = ChunkContent(text="Hello world", token_count=2)
        chunk = Chunk.create(document_id="doc-1", content=content, position=0)
        assert chunk.id
        assert chunk.document_id == "doc-1"
        assert chunk.position == 0
        assert chunk.embedding is None

    def test_chunk_set_embedding_should_update_embedding_when_called(self) -> None:
        content = ChunkContent(text="Hello world", token_count=2)
        chunk = Chunk.create(document_id="doc-1", content=content, position=0)
        embedding = Embedding.from_list([0.1, 0.2])
        chunk.set_embedding(embedding)
        assert chunk.embedding == embedding

    def test_chunk_has_embedding_should_return_false_when_none(self) -> None:
        content = ChunkContent(text="Hello world", token_count=2)
        chunk = Chunk.create(document_id="doc-1", content=content, position=0)
        assert chunk.has_embedding() is False


class TestSplitTextIntoChunks:
    def test_should_return_empty_list_when_text_is_empty(self) -> None:
        assert split_text_into_chunks("") == []

    def test_should_return_empty_list_when_text_is_whitespace(self) -> None:
        assert split_text_into_chunks("   ") == []

    def test_should_return_single_chunk_when_text_fits_in_chunk_size(self) -> None:
        text = "word " * 10
        result = split_text_into_chunks(text, chunk_size=500)
        assert len(result) == 1
        assert result[0] == " ".join(["word"] * 10)

    def test_should_split_into_multiple_chunks_when_text_exceeds_chunk_size(
        self,
    ) -> None:
        text = " ".join(f"w{i}" for i in range(20))
        result = split_text_into_chunks(text, chunk_size=10, overlap=0)
        assert len(result) == 2
        assert result[0] == " ".join(f"w{i}" for i in range(10))
        assert result[1] == " ".join(f"w{i}" for i in range(10, 20))

    def test_should_create_overlapping_chunks_when_overlap_specified(self) -> None:
        text = " ".join(f"w{i}" for i in range(15))
        result = split_text_into_chunks(text, chunk_size=10, overlap=5)
        assert len(result) == 3
        assert result[0] == " ".join(f"w{i}" for i in range(0, 10))
        assert result[1] == " ".join(f"w{i}" for i in range(5, 15))
        # Third chunk contains the tail from position 10
        assert result[2] == " ".join(f"w{i}" for i in range(10, 15))
