from io import BytesIO

import pytest
from fastapi import HTTPException, UploadFile

from documentor.adapters.api.file_validation import validate_upload_file


def _make_upload_file(
    content: bytes, filename: str, content_type: str = "application/octet-stream"
) -> UploadFile:
    return UploadFile(
        file=BytesIO(content),
        filename=filename,
        headers={"content-type": content_type},
    )


@pytest.mark.asyncio
async def test_validate_should_return_content_when_valid_txt() -> None:
    file = _make_upload_file(b"Hello, world!", "readme.txt")

    result = await validate_upload_file(file)

    assert result == b"Hello, world!"


@pytest.mark.asyncio
async def test_validate_should_return_content_when_valid_md() -> None:
    file = _make_upload_file(b"# Title\nContent", "guide.md")

    result = await validate_upload_file(file)

    assert result == b"# Title\nContent"


@pytest.mark.asyncio
async def test_validate_should_return_content_when_valid_html() -> None:
    file = _make_upload_file(b"<html></html>", "page.html")

    result = await validate_upload_file(file)

    assert result == b"<html></html>"


@pytest.mark.asyncio
async def test_validate_should_return_content_when_valid_rst() -> None:
    file = _make_upload_file(b"Title\n=====\n", "doc.rst")

    result = await validate_upload_file(file)

    assert result == b"Title\n=====\n"


@pytest.mark.asyncio
async def test_validate_should_return_content_when_valid_pdf() -> None:
    file = _make_upload_file(b"%PDF-1.4 fake pdf content", "doc.pdf")

    result = await validate_upload_file(file)

    assert result == b"%PDF-1.4 fake pdf content"


@pytest.mark.asyncio
async def test_validate_should_reject_unsupported_extension() -> None:
    file = _make_upload_file(b"data", "file.exe")

    with pytest.raises(HTTPException) as exc_info:
        await validate_upload_file(file)

    assert exc_info.value.status_code == 400
    assert "Unsupported file extension" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_validate_should_reject_oversized_file() -> None:
    content = b"x" * (10 * 1024 * 1024 + 1)
    file = _make_upload_file(content, "big.txt")

    with pytest.raises(HTTPException) as exc_info:
        await validate_upload_file(file)

    assert exc_info.value.status_code == 400
    assert "maximum size" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_validate_should_reject_empty_file() -> None:
    file = _make_upload_file(b"", "empty.txt")

    with pytest.raises(HTTPException) as exc_info:
        await validate_upload_file(file)

    assert exc_info.value.status_code == 400
    assert "empty" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_validate_should_reject_pdf_with_wrong_magic_bytes() -> None:
    file = _make_upload_file(b"NOT-A-PDF-FILE", "fake.pdf")

    with pytest.raises(HTTPException) as exc_info:
        await validate_upload_file(file)

    assert exc_info.value.status_code == 400
    assert "valid PDF" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_validate_should_reject_text_with_invalid_utf8() -> None:
    file = _make_upload_file(b"\x80\x81\x82invalid", "broken.txt")

    with pytest.raises(HTTPException) as exc_info:
        await validate_upload_file(file)

    assert exc_info.value.status_code == 400
    assert "UTF-8" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_validate_should_reject_no_extension() -> None:
    file = _make_upload_file(b"data", "noext")

    with pytest.raises(HTTPException) as exc_info:
        await validate_upload_file(file)

    assert exc_info.value.status_code == 400
    assert "Unsupported file extension" in str(exc_info.value.detail)
