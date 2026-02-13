import pymupdf
import pytest

from documentor.domain.exceptions import DocumentLoadError
from documentor.domain.models.document import SourceType
from documentor.infrastructure.external.file_document_loader import FileDocumentLoader


@pytest.mark.asyncio
async def test_load_should_return_content_when_valid_txt_file() -> None:
    content = b"Hello, world!"
    loader = FileDocumentLoader(content, "readme.txt")

    result = await loader.load("sha256:abc123")

    assert result.content == "Hello, world!"
    assert result.title == "readme"
    assert result.source_type == SourceType.FILE


@pytest.mark.asyncio
async def test_load_should_return_content_when_valid_md_file() -> None:
    content = b"# My Title\n\nSome content here."
    loader = FileDocumentLoader(content, "guide.md")

    result = await loader.load("sha256:abc123")

    assert result.content == "# My Title\n\nSome content here."
    assert result.title == "My Title"
    assert result.source_type == SourceType.FILE


@pytest.mark.asyncio
async def test_load_should_use_filename_stem_when_md_has_no_heading() -> None:
    content = b"No heading here, just plain text."
    loader = FileDocumentLoader(content, "notes.md")

    result = await loader.load("sha256:abc123")

    assert result.title == "notes"


@pytest.mark.asyncio
async def test_load_should_return_content_when_valid_rst_file() -> None:
    content = b"# RST Title\n\nSome RST content."
    loader = FileDocumentLoader(content, "index.rst")

    result = await loader.load("sha256:abc123")

    assert result.title == "RST Title"
    assert result.source_type == SourceType.FILE


@pytest.mark.asyncio
async def test_load_should_return_content_when_valid_html_file() -> None:
    content = b"<html><body><p>Hello</p></body></html>"
    loader = FileDocumentLoader(content, "page.html")

    result = await loader.load("sha256:abc123")

    assert result.content == "<html><body><p>Hello</p></body></html>"
    assert result.title == "page"
    assert result.source_type == SourceType.FILE


@pytest.mark.asyncio
async def test_load_should_extract_text_when_valid_pdf() -> None:
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Hello from PDF")
    pdf_bytes = doc.tobytes()
    doc.close()

    loader = FileDocumentLoader(pdf_bytes, "document.pdf")

    result = await loader.load("sha256:abc123")

    assert "Hello from PDF" in result.content
    assert result.title == "document"
    assert result.source_type == SourceType.FILE


@pytest.mark.asyncio
async def test_load_should_raise_when_invalid_utf8_text() -> None:
    content = b"\x80\x81\x82invalid"
    loader = FileDocumentLoader(content, "broken.txt")

    with pytest.raises(DocumentLoadError, match="Failed to extract content"):
        await loader.load("sha256:abc123")


@pytest.mark.asyncio
async def test_load_should_raise_when_corrupt_pdf() -> None:
    content = b"%PDF-not-a-real-pdf"
    loader = FileDocumentLoader(content, "corrupt.pdf")

    with pytest.raises(DocumentLoadError, match="Failed to extract content"):
        await loader.load("sha256:abc123")


@pytest.mark.asyncio
async def test_load_should_raise_when_unsupported_extension() -> None:
    loader = FileDocumentLoader(b"data", "file.xyz")

    with pytest.raises(DocumentLoadError, match="Unsupported file extension"):
        await loader.load("sha256:abc123")
