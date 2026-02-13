from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import AsyncClient

from documentor.application.dtos import IngestDocumentationInput
from documentor.domain.exceptions import DuplicateDocumentError

# --- File upload tests ---


@pytest.mark.asyncio
async def test_ingest_should_return_document_when_valid_source(
    client: AsyncClient,
    mock_ingest_documentation: AsyncMock,
) -> None:
    response = await client.post(
        "/ingest/url", json={"source": "https://example.com/docs"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["document"]["id"] == "doc-1"
    assert data["document"]["title"] == "Example Docs"
    assert data["chunks_created"] == 3
    mock_ingest_documentation.execute.assert_called_once_with(
        IngestDocumentationInput(
            source="https://example.com/docs", on_duplicate="reject"
        )
    )


@pytest.mark.asyncio
async def test_ingest_should_return_422_when_source_missing(
    client: AsyncClient,
) -> None:
    response = await client.post("/ingest/url", json={})

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_ingest_should_return_409_when_duplicate_and_reject(
    client: AsyncClient,
    mock_ingest_documentation: AsyncMock,
) -> None:
    mock_ingest_documentation.execute.side_effect = DuplicateDocumentError(
        "https://example.com/docs"
    )

    response = await client.post(
        "/ingest/url", json={"source": "https://example.com/docs"}
    )

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_ingest_should_pass_on_duplicate_to_use_case(
    client: AsyncClient,
    mock_ingest_documentation: AsyncMock,
) -> None:
    response = await client.post(
        "/ingest/url",
        json={"source": "https://example.com/docs", "on_duplicate": "skip"},
    )

    assert response.status_code == 200
    mock_ingest_documentation.execute.assert_called_once_with(
        IngestDocumentationInput(source="https://example.com/docs", on_duplicate="skip")
    )


@pytest.mark.asyncio
async def test_list_documents_should_return_documents(
    client: AsyncClient,
    mock_list_documents: AsyncMock,
) -> None:
    response = await client.get("/documents")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "doc-1"
    assert data[0]["title"] == "Example Docs"
    mock_list_documents.execute.assert_called_once()


@pytest.mark.asyncio
async def test_list_documents_should_return_empty_list(
    client: AsyncClient,
    mock_list_documents: AsyncMock,
) -> None:
    mock_list_documents.execute.return_value = []

    response = await client.get("/documents")

    assert response.status_code == 200
    assert response.json() == []


# --- File upload endpoint tests ---


@pytest.mark.asyncio
async def test_ingest_file_should_return_document_when_valid_txt(
    client: AsyncClient,
    mock_ingest_file_documentation: MagicMock,
) -> None:
    response = await client.post(
        "/ingest/file",
        files={"file": ("readme.txt", b"Hello, world!", "text/plain")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["document"]["id"] == "doc-file-1"
    assert data["document"]["source_type"] == "file"
    assert data["chunks_created"] == 2

    mock_use_case = mock_ingest_file_documentation._mock_use_case
    mock_use_case.execute.assert_called_once()
    call_input = mock_use_case.execute.call_args[0][0]
    assert call_input.source.startswith("sha256:")
    assert call_input.on_duplicate == "reject"


@pytest.mark.asyncio
async def test_ingest_file_should_return_400_when_unsupported_extension(
    client: AsyncClient,
) -> None:
    response = await client.post(
        "/ingest/file",
        files={"file": ("script.exe", b"MZ\x90\x00", "application/octet-stream")},
    )

    assert response.status_code == 400
    assert "Unsupported file extension" in response.json()["detail"]


@pytest.mark.asyncio
async def test_ingest_file_should_return_400_when_empty_file(
    client: AsyncClient,
) -> None:
    response = await client.post(
        "/ingest/file",
        files={"file": ("empty.txt", b"", "text/plain")},
    )

    assert response.status_code == 400
    assert "empty" in response.json()["detail"]


@pytest.mark.asyncio
async def test_ingest_file_should_return_400_when_oversized(
    client: AsyncClient,
) -> None:
    content = b"x" * (10 * 1024 * 1024 + 1)
    response = await client.post(
        "/ingest/file",
        files={"file": ("big.txt", content, "text/plain")},
    )

    assert response.status_code == 400
    assert "maximum size" in response.json()["detail"]


@pytest.mark.asyncio
async def test_ingest_file_should_return_400_when_pdf_with_wrong_magic_bytes(
    client: AsyncClient,
) -> None:
    response = await client.post(
        "/ingest/file",
        files={"file": ("fake.pdf", b"NOT-A-PDF", "application/pdf")},
    )

    assert response.status_code == 400
    assert "valid PDF" in response.json()["detail"]


@pytest.mark.asyncio
async def test_ingest_file_should_return_409_when_duplicate_hash(
    client: AsyncClient,
    mock_ingest_file_documentation: MagicMock,
) -> None:
    mock_use_case = mock_ingest_file_documentation._mock_use_case
    mock_use_case.execute.side_effect = DuplicateDocumentError("sha256:abc123")

    response = await client.post(
        "/ingest/file",
        files={"file": ("readme.txt", b"Hello, world!", "text/plain")},
    )

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_ingest_file_should_return_422_when_no_file_provided(
    client: AsyncClient,
) -> None:
    response = await client.post("/ingest/file")

    assert response.status_code == 422
