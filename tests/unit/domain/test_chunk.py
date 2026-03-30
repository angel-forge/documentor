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

    def test_create_should_set_language_when_provided(self) -> None:
        content = ChunkContent(text="Hello world", token_count=2)
        chunk = Chunk.create(document_id="doc-1", content=content, position=0, language="french")
        assert chunk.language == "french"

    def test_create_should_default_language_to_english_when_not_provided(self) -> None:
        content = ChunkContent(text="Hello world", token_count=2)
        chunk = Chunk.create(document_id="doc-1", content=content, position=0)
        assert chunk.language == "english"

    def test_language_field_is_mutable(self) -> None:
        content = ChunkContent(text="Hello world", token_count=2)
        chunk = Chunk.create(document_id="doc-1", content=content, position=0)
        chunk.language = "spanish"
        assert chunk.language == "spanish"


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

    def test_should_split_by_words_when_no_markdown_structure(self) -> None:
        # Plain text without headings or code fences uses word-boundary split (fallback).
        text = " ".join(f"w{i}" for i in range(20))
        result = split_text_into_chunks(text, chunk_size=10, overlap=0)
        assert len(result) == 2
        assert result[0] == " ".join(f"w{i}" for i in range(10))
        assert result[1] == " ".join(f"w{i}" for i in range(10, 20))

    def test_should_preserve_overlap_when_using_word_fallback(self) -> None:
        # Overlap param must work unchanged on the fallback path.
        text = " ".join(f"w{i}" for i in range(15))
        result = split_text_into_chunks(text, chunk_size=10, overlap=5)
        # w0..w9 | w5..w14 | w10..w14
        assert result[0].split()[0] == "w0"
        assert result[1].split()[0] == "w5"

    def test_should_use_word_count_when_no_token_counter(self) -> None:
        # Without token_counter, chunk_size is word count — same as before.
        text = " ".join(["hello"] * 20)
        result = split_text_into_chunks(text, chunk_size=10, overlap=0)
        assert len(result) == 2
        for chunk in result:
            assert len(chunk.split()) == 10

    def test_should_accept_token_counter_parameter_without_error(self) -> None:
        # The parameter exists and is accepted; behavioral depth tested in markdown tests.
        counter_calls: list[str] = []

        def counting_counter(t: str) -> int:
            counter_calls.append(t)
            return len(t.split())

        text = " ".join(f"w{i}" for i in range(10))
        result = split_text_into_chunks(text, chunk_size=5, overlap=0, token_counter=counting_counter)
        assert len(result) == 2


class TestMarkdownChunking:
    """Tests for the structure-aware markdown chunking path."""

    # ------------------------------------------------------------------
    # 2.1 — _parse_markdown_sections behaviour (tested via full pipeline)
    # ------------------------------------------------------------------

    def test_should_create_section_per_heading_when_multiple_headings(self) -> None:
        # Two sibling sections each 300 words with chunk_size=400 — too large to merge
        # (combined 600 > 400), so each is a separate chunk.
        body = " ".join(["word"] * 300)
        text = f"## Section A\n\n{body}\n\n## Section B\n\n{body}\n"
        result = split_text_into_chunks(text, chunk_size=400, overlap=0)
        assert len(result) == 2
        assert "## Section A" in result[0]
        assert "## Section B" in result[1]

    def test_should_track_heading_hierarchy_when_nested_headings(self) -> None:
        text = "# Parent\n\n## Child\n\nBody of child.\n"
        result = split_text_into_chunks(text, chunk_size=500, overlap=0)
        # The child chunk must carry the parent as context prefix
        assert len(result) == 1
        assert "# Parent" in result[0]
        assert "## Child" in result[0]
        assert "Body of child." in result[0]

    def test_should_not_detect_headings_inside_code_blocks(self) -> None:
        text = "## Real Heading\n\n```python\n# This is a comment, not a heading\ncode = True\n```\n"
        result = split_text_into_chunks(text, chunk_size=500, overlap=0)
        # Only one real heading → only one chunk (or zero if only heading with body)
        # The code block comment must not create a new section
        assert len(result) == 1
        assert "# This is a comment" in result[0]

    def test_should_preserve_content_before_first_heading(self) -> None:
        text = "Preamble text before any heading.\n\n# First Heading\n\nHeading body.\n"
        result = split_text_into_chunks(text, chunk_size=500, overlap=0)
        # Preamble has no heading context → separate chunk (no prefix)
        # First heading chunk has heading as context
        preamble_chunks = [c for c in result if "Preamble text" in c]
        assert len(preamble_chunks) == 1
        # Preamble chunk should NOT have a heading prefix
        assert not preamble_chunks[0].startswith(">")

    def test_should_return_empty_list_when_text_is_empty(self) -> None:
        assert split_text_into_chunks("") == []

    def test_should_return_empty_list_when_text_is_whitespace(self) -> None:
        assert split_text_into_chunks("   \n\t  ") == []

    def test_should_handle_document_with_only_headings_no_content(self) -> None:
        text = "# H1\n## H2\n### H3\n"
        result = split_text_into_chunks(text, chunk_size=500, overlap=0)
        assert result == []

    # ------------------------------------------------------------------
    # 2.2 — _split_section behaviour
    # ------------------------------------------------------------------

    def test_should_split_large_section_at_paragraph_boundaries(self) -> None:
        # A section with 3 paragraphs of 200 words each, chunk_size=250 words.
        # Must split at paragraph boundary, not mid-word.
        paragraph = " ".join(["word"] * 200)
        text = f"## Big Section\n\n{paragraph}\n\n{paragraph}\n\n{paragraph}\n"
        result = split_text_into_chunks(text, chunk_size=250, overlap=0)
        # 600 total words / 250 → should produce at least 2 chunks
        assert len(result) >= 2
        # Each chunk must carry the heading prefix
        for chunk in result:
            assert "## Big Section" in chunk

    def test_should_not_split_code_blocks(self) -> None:
        # A code block of 600 words inside a section with chunk_size=200.
        # The code block must not be split.
        code_lines = "\n".join([f"    x_{i} = {i}  # variable" for i in range(100)])
        text = f"## Code Section\n\n```python\n{code_lines}\n```\n"
        result = split_text_into_chunks(text, chunk_size=200, overlap=0)
        # Must produce exactly one chunk containing the full code block
        assert len(result) == 1
        assert "```python" in result[0]
        assert "```" in result[0]

    def test_should_emit_oversized_code_block_as_single_chunk(self) -> None:
        # REQ-SC-18 / SC-11: a 2000-word code block → one chunk, no split
        code_lines = "\n".join([f"var_{i} = {i}" for i in range(500)])
        text = f"## Code Heavy\n\n```\n{code_lines}\n```\n"
        result = split_text_into_chunks(text, chunk_size=500, overlap=0)
        assert len(result) == 1
        assert "```" in result[0]

    def test_should_merge_small_adjacent_chunks(self) -> None:
        # SC-09: three ## sections each ~50 words, chunk_size=500 → expect 1 chunk
        small_body = " ".join(["word"] * 50)
        text = (
            f"## Sec A\n\n{small_body}\n\n"
            f"## Sec B\n\n{small_body}\n\n"
            f"## Sec C\n\n{small_body}\n"
        )
        result = split_text_into_chunks(text, chunk_size=500, overlap=0)
        # Three small sections — should merge into 1 chunk (150 words < 500)
        assert len(result) == 1

    # ------------------------------------------------------------------
    # 2.3 — markdown detection and context injection
    # ------------------------------------------------------------------

    def test_should_use_markdown_chunking_when_headings_present(self) -> None:
        text = "# Title\n\nSome body text here.\n"
        result = split_text_into_chunks(text, chunk_size=500, overlap=0)
        # Heading-path: result has one chunk with heading as context
        assert len(result) == 1
        assert "# Title" in result[0]

    def test_should_use_word_fallback_when_hash_is_not_heading(self) -> None:
        # #hashtag (no space after #) is NOT a markdown heading
        text = "#hashtag content without real headings here"
        result = split_text_into_chunks(text, chunk_size=500, overlap=0)
        assert len(result) == 1
        # No structural prefix — plain word-boundary output
        assert not result[0].startswith(">")

    def test_should_prepend_heading_chain_when_section_has_headings(self) -> None:
        # SC-02: # Parent → ## Child body → chunk has "# Parent\n## Child\n" prefix
        text = "# Parent\n\n## Child\n\nBody of child.\n"
        result = split_text_into_chunks(text, chunk_size=500, overlap=0)
        assert len(result) == 1
        assert result[0].startswith("# Parent\n## Child\n")
        assert "Body of child." in result[0]

    def test_should_not_prepend_heading_when_section_has_no_headings(self) -> None:
        text = "Preamble without any heading.\n\n# Section\n\nBody.\n"
        result = split_text_into_chunks(text, chunk_size=500, overlap=0)
        preamble_chunks = [c for c in result if "Preamble" in c]
        assert len(preamble_chunks) == 1
        # Preamble chunk has no heading prefix
        assert not preamble_chunks[0].startswith("#")

    def test_should_prepend_heading_to_each_chunk_when_section_split(self) -> None:
        # SC-04: large prose section split into multiple chunks; each gets heading prefix
        paragraph = " ".join(["word"] * 300)
        text = f"## Large Section\n\n{paragraph}\n\n{paragraph}\n\n{paragraph}\n"
        result = split_text_into_chunks(text, chunk_size=400, overlap=0)
        assert len(result) >= 2
        for chunk in result:
            assert "## Large Section" in chunk

    # ------------------------------------------------------------------
    # 2.4 — edge cases and scenario coverage
    # ------------------------------------------------------------------

    def test_should_handle_deeply_nested_headings(self) -> None:
        # SC-10 / REQ-SC-19: h1 > h2 > h3 > h4 hierarchy
        text = "# H1\n\n## H2\n\n### H3\n\n#### H4\n\nDeep body.\n"
        result = split_text_into_chunks(text, chunk_size=500, overlap=0)
        assert len(result) == 1
        # Heading chain must include all ancestor levels
        assert "# H1" in result[0]
        assert "## H2" in result[0]
        assert "### H3" in result[0]
        assert "#### H4" in result[0]
        assert "Deep body." in result[0]

    def test_should_handle_non_sequential_heading_levels(self) -> None:
        # REQ-SC-19: # Top directly followed by ### Deep (no ## in between)
        text = "# Top\n\n### Deep\n\nBody text.\n"
        result = split_text_into_chunks(text, chunk_size=500, overlap=0)
        assert len(result) == 1
        # Chain reflects actually seen headings: Top → Deep
        assert "# Top" in result[0]
        assert "### Deep" in result[0]
        assert "Body text." in result[0]

    def test_should_merge_small_sections_into_single_chunk(self) -> None:
        # SC-09 / REQ-SC-09: three ## sections 50 words each → 1 merged chunk
        small_body = " ".join(["word"] * 50)
        text = (
            f"## Alpha\n\n{small_body}\n\n"
            f"## Beta\n\n{small_body}\n\n"
            f"## Gamma\n\n{small_body}\n"
        )
        result = split_text_into_chunks(text, chunk_size=500, overlap=0)
        assert len(result) == 1

    def test_should_emit_each_sibling_section_as_separate_chunk_when_large(
        self,
    ) -> None:
        # SC-01 adapted: two ## sections each 300 words, chunk_size=350 → 2 chunks
        large_body = " ".join(["word"] * 300)
        text = f"## Section A\n\n{large_body}\n\n## Section B\n\n{large_body}\n"
        result = split_text_into_chunks(text, chunk_size=350, overlap=0)
        assert len(result) == 2
        assert "## Section A" in result[0]
        assert "## Section B" in result[1]

    def test_should_not_repeat_heading_when_chunk_content_has_no_heading_prefix(
        self,
    ) -> None:
        # REQ-SC-05: the heading chain prefix is ANCESTOR headings only.
        # The section heading itself appears in the prefix, not duplicated in body.
        text = "# Root\n\n## Sub\n\nContent body.\n"
        result = split_text_into_chunks(text, chunk_size=500, overlap=0)
        assert len(result) == 1
        chunk = result[0]
        # "## Sub" should appear exactly once in the chunk (as context prefix line)
        assert chunk.count("## Sub") == 1

    def test_should_fallback_to_word_split_when_large_prose_has_no_paragraphs(
        self,
    ) -> None:
        # SC-12 / REQ-SC-07: a single long line with no paragraph breaks inside
        # a markdown section must be split at word boundaries.
        long_line = " ".join(f"w{i}" for i in range(600))
        text = f"## Dense Section\n\n{long_line}\n"
        result = split_text_into_chunks(text, chunk_size=250, overlap=0)
        # 600 words / 250 chunk_size → at least 2 chunks
        assert len(result) >= 2
        # Every chunk must carry the heading prefix
        for chunk in result:
            assert "## Dense Section" in chunk
