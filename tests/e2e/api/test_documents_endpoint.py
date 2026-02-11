from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

from documentor.application.dtos import IngestDocumentationInput


@pytest.mark.asyncio
async def test_ingest_should_return_document_when_valid_source(
    client: AsyncClient,
    mock_ingest_documentation: AsyncMock,
) -> None:
    response = await client.post("/ingest", json={"source": "https://example.com/docs"})

    assert response.status_code == 200
    data = response.json()
    assert data["document"]["id"] == "doc-1"
    assert data["document"]["title"] == "Example Docs"
    assert data["chunks_created"] == 3
    mock_ingest_documentation.execute.assert_called_once_with(
        IngestDocumentationInput(source="https://example.com/docs")
    )


@pytest.mark.asyncio
async def test_ingest_should_return_422_when_source_missing(
    client: AsyncClient,
) -> None:
    response = await client.post("/ingest", json={})

    assert response.status_code == 422


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
