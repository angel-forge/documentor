import re
from collections.abc import Callable
from dataclasses import dataclass, field
from uuid_utils import uuid7

from documentor.domain.exceptions import InvalidChunkError, InvalidEmbeddingError


@dataclass(frozen=True)
class Embedding:
    vector: tuple[float, ...]
    dimension: int

    def __post_init__(self) -> None:
        if len(self.vector) != self.dimension:
            raise InvalidEmbeddingError(
                f"Vector length {len(self.vector)} does not match dimension {self.dimension}"
            )

    @classmethod
    def from_list(cls, values: list[float]) -> "Embedding":
        return cls(vector=tuple(values), dimension=len(values))


@dataclass(frozen=True)
class ChunkContent:
    text: str
    token_count: int

    def __post_init__(self) -> None:
        if not self.text or not self.text.strip():
            raise InvalidChunkError("Chunk text cannot be empty")
        if self.token_count <= 0:
            raise InvalidChunkError("Token count must be greater than 0")


@dataclass
class Chunk:
    id: str
    document_id: str
    content: ChunkContent
    position: int
    embedding: Embedding | None = None
    language: str = "english"

    @classmethod
    def create(
        cls,
        document_id: str,
        content: ChunkContent,
        position: int,
        language: str = "english",
    ) -> "Chunk":
        return cls(
            id=str(uuid7()),
            document_id=document_id,
            content=content,
            position=position,
            language=language,
        )

    def set_embedding(self, embedding: Embedding) -> None:
        self.embedding = embedding

    def has_embedding(self) -> bool:
        return self.embedding is not None


# ---------------------------------------------------------------------------
# Internal helpers — not part of the public API
# ---------------------------------------------------------------------------


@dataclass
class _Section:
    """Internal structure produced by the markdown parser (not a domain model).

    heading_chain: ordered list of (level, text) pairs from document root to this section's parent.
    content: the text body of this section (without the heading line itself).
    """

    heading_chain: list[tuple[int, str]] = field(default_factory=list)
    content: str = ""


def _count_words(text: str) -> int:
    """Return the number of whitespace-separated words in *text*."""
    return len(text.split())


def _is_heading_line(line: str) -> tuple[bool, int, str]:
    """Return (is_heading, level, text) for a line."""
    stripped = line.strip()
    m = re.match(r'^(#{1,6})\s+(\S.*)', stripped)
    if m:
        return True, len(m.group(1)), m.group(2).strip()
    return False, 0, ""


def _is_code_fence(line: str) -> bool:
    """Return True if the line is a fenced code block delimiter (``` ...)."""
    return line.strip().startswith("```")


def _parse_markdown_sections(text: str) -> list[_Section]:
    """Phase 1: Parse markdown text into sections using a line-by-line state machine.

    Each heading starts a new Section. Content (including code blocks) accumulates
    into the current section. Text before the first heading gets a Section with an
    empty heading_chain.
    """
    lines = text.splitlines(keepends=True)

    sections: list[_Section] = []
    # heading_stack stores (level, text) pairs for the active hierarchy
    heading_stack: list[tuple[int, str]] = []
    in_code_block = False
    current_content_lines: list[str] = []

    def _flush_section() -> None:
        """Persist accumulated content into a new Section."""
        content = "".join(current_content_lines).strip()
        if content:
            sections.append(_Section(heading_chain=list(heading_stack), content=content))

    for line in lines:
        # Toggle code-block state (ignore heading detection inside blocks)
        if _is_code_fence(line):
            in_code_block = not in_code_block
            current_content_lines.append(line)
            continue

        if not in_code_block:
            is_heading, level, heading_text = _is_heading_line(line)
            if is_heading:
                # Flush content accumulated before this heading
                _flush_section()
                current_content_lines = []

                # Update heading stack: pop all entries with level >= this level
                while heading_stack and heading_stack[-1][0] >= level:
                    heading_stack.pop()
                heading_stack.append((level, heading_text))
                # The heading line itself is NOT added to content (it becomes context prefix)
                continue

        current_content_lines.append(line)

    # Flush any remaining content
    _flush_section()

    return sections


def _split_by_words(
    text: str,
    chunk_size: int,
    overlap: int,
) -> list[str]:
    """Split *text* into overlapping chunks at word boundaries."""
    words = text.split()
    if not words:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk_text = " ".join(words[start:end])
        chunks.append(chunk_text)
        start += chunk_size - overlap

    return chunks


def _split_paragraphs(text: str) -> list[str]:
    """Split text at blank-line paragraph boundaries, keeping code blocks intact."""
    lines = text.splitlines(keepends=True)
    in_code_block = False
    paragraphs: list[str] = []
    current: list[str] = []

    for line in lines:
        if _is_code_fence(line):
            in_code_block = not in_code_block
            current.append(line)
            continue

        if not in_code_block and line.strip() == "":
            # Blank line = paragraph boundary (only outside code blocks)
            para = "".join(current).strip()
            if para:
                paragraphs.append(para)
            current = []
        else:
            current.append(line)

    # Flush remaining
    remaining = "".join(current).strip()
    if remaining:
        paragraphs.append(remaining)

    return paragraphs if paragraphs else [text.strip()]


def _split_lines_preserving_code(text: str) -> list[str]:
    """Split text at line boundaries, but treat code blocks as single units."""
    lines = text.splitlines(keepends=True)
    in_code_block = False
    result: list[str] = []
    code_block_lines: list[str] = []

    for line in lines:
        if _is_code_fence(line):
            if not in_code_block:
                # Start of code block
                in_code_block = True
                code_block_lines = [line]
            else:
                # End of code block
                in_code_block = False
                code_block_lines.append(line)
                result.append("".join(code_block_lines))
                code_block_lines = []
            continue

        if in_code_block:
            code_block_lines.append(line)
        else:
            stripped = line.strip()
            if stripped:
                result.append(stripped)

    # Flush unclosed code block (shouldn't happen in well-formed markdown)
    if code_block_lines:
        result.append("".join(code_block_lines))

    return result if result else [text.strip()]


def _split_section(
    section: _Section,
    chunk_size: int,
    size_fn: Callable[[str], int],
) -> list[str]:
    """Phase 2: Split a single section body into chunks.

    Split order: paragraph boundaries → line boundaries → word boundaries.
    Never split inside a fenced code block.
    After splitting, greedily merge adjacent sub-chunks up to chunk_size.
    Returns list[str] of body texts (heading prefix not added here).
    """
    content = section.content
    if not content.strip():
        return []

    # If fits in one chunk, return as-is
    if size_fn(content) <= chunk_size:
        return [content]

    # --- Split at paragraph boundaries, code-block-aware ---
    paragraphs = _split_paragraphs(content)

    # --- If any single paragraph is still too large, split further ---
    candidate_chunks: list[str] = []
    for para in paragraphs:
        if size_fn(para) <= chunk_size:
            candidate_chunks.append(para)
        else:
            # Check if it's a code block — if so, keep it as one oversized chunk
            stripped = para.strip()
            if stripped.startswith("```") and stripped.endswith("```") and stripped.count("```") >= 2:
                # Atomic code block — never split
                candidate_chunks.append(para)
                continue

            # Try splitting at line boundaries
            lines_split = _split_lines_preserving_code(para)
            for line_chunk in lines_split:
                if size_fn(line_chunk) <= chunk_size:
                    candidate_chunks.append(line_chunk)
                else:
                    # Check if this line chunk is itself a code block
                    stripped_lc = line_chunk.strip()
                    if stripped_lc.startswith("```") and stripped_lc.endswith("```"):
                        # Oversized code block — emit as-is
                        candidate_chunks.append(line_chunk)
                    else:
                        # Fall back to word-boundary split for an oversized plain line
                        word_chunks = _split_by_words(line_chunk, chunk_size, overlap=0)
                        candidate_chunks.extend(word_chunks)

    # --- Greedy merge: combine adjacent candidates up to chunk_size ---
    merged: list[str] = []
    buffer = ""
    for candidate in candidate_chunks:
        candidate = candidate.strip()
        if not candidate:
            continue
        if not buffer:
            buffer = candidate
        else:
            combined = buffer + "\n\n" + candidate
            if size_fn(combined) <= chunk_size:
                buffer = combined
            else:
                merged.append(buffer)
                buffer = candidate

    if buffer:
        merged.append(buffer)

    return merged


def _heading_prefix(heading_chain: list[tuple[int, str]]) -> str:
    """Format heading chain as ATX heading lines using the original heading levels.

    Example: [(1, "API Reference"), (3, "Authentication")] →
             "# API Reference\n### Authentication\n"
    """
    if not heading_chain:
        return ""
    lines = [f"{'#' * level} {text}" for level, text in heading_chain]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def split_text_into_chunks(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50,
    token_counter: Callable[[str], int] | None = None,
) -> list[str]:
    """Split text into chunks using structure-aware markdown parsing when possible.

    When markdown headings are detected, splits at structural boundaries and
    prepends heading context to each chunk. Falls back to word-boundary splitting
    for plain text.
    """
    if not text or not text.strip():
        return []

    # Resolve the size function once
    size_fn: Callable[[str], int] = token_counter if token_counter is not None else _count_words

    # Detect markdown structure: any ATX heading triggers the structured path
    has_markdown = bool(re.search(r'^#{1,6}\s', text, re.MULTILINE))

    if not has_markdown:
        return _split_by_words(text, chunk_size, overlap)

    # --- Structured markdown path ---
    sections = _parse_markdown_sections(text)

    # Merge adjacent small sections (REQ-SC-09): sections whose combined size ≤ chunk_size
    # are greedily combined before splitting into output chunks.
    result: list[str] = _merge_and_emit_sections(sections, chunk_size, size_fn)

    return result


def _merge_and_emit_sections(
    sections: list[_Section],
    chunk_size: int,
    size_fn: Callable[[str], int],
) -> list[str]:
    """Merge small adjacent sections and emit chunks with heading context.

    Adjacent sections whose combined content size is ≤ chunk_size are merged into
    a single chunk. Large sections are split by _split_section.
    """
    result: list[str] = []

    # Buffer for accumulating small sections to merge
    # A "merge group" is a list of (heading_chain, body_text) pairs that will be
    # combined into one chunk.
    merge_buffer: list[tuple[list[tuple[int, str]], str]] = []
    merge_buffer_size = 0

    def _flush_merge_buffer() -> None:
        nonlocal merge_buffer_size
        if not merge_buffer:
            return
        if len(merge_buffer) == 1:
            chain, body = merge_buffer[0]
            prefix = _heading_prefix(chain)
            chunk_text = (prefix + "\n" + body if prefix else body).strip()
            if chunk_text:
                result.append(chunk_text)
        else:
            # Combine multiple small sections into one chunk
            parts: list[str] = []
            for chain, body in merge_buffer:
                prefix = _heading_prefix(chain)
                if prefix:
                    parts.append(prefix + "\n" + body)
                else:
                    parts.append(body)
            combined = "\n\n".join(parts).strip()
            if combined:
                result.append(combined)
        merge_buffer.clear()
        merge_buffer_size = 0

    for section in sections:
        body_size = size_fn(section.content)

        if body_size <= chunk_size:
            # Small section — try to merge with buffer
            if merge_buffer_size + body_size <= chunk_size:
                merge_buffer.append((section.heading_chain, section.content))
                merge_buffer_size += body_size
            else:
                # Buffer full — flush and start new buffer
                _flush_merge_buffer()
                merge_buffer.append((section.heading_chain, section.content))
                merge_buffer_size = body_size
        else:
            # Large section — flush buffer first, then split this section
            _flush_merge_buffer()
            body_chunks = _split_section(section, chunk_size, size_fn)
            prefix = _heading_prefix(section.heading_chain)
            for body in body_chunks:
                body = body.strip()
                if not body:
                    continue
                chunk_text = (prefix + "\n" + body if prefix else body).strip()
                result.append(chunk_text)

    # Flush any remaining buffered sections
    _flush_merge_buffer()

    return result
