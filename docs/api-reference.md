# API Reference

Base URL: `http://localhost:8000`

Interactive docs available at `/docs` (Swagger UI) and `/redoc` (ReDoc) when the server is running.

---

## GET /health

Health check.

**Response** `200`

```json
{
  "status": "ok"
}
```

---

## POST /ingest

Ingest documentation from a URL or file path.

**Request**

```json
{
  "source": "https://raw.githubusercontent.com/tiangolo/fastapi/master/README.md"
}
```

**Response** `200`

```json
{
  "document": {
    "id": "019c4dcd-428f-70e2-ad28-27e11a1c14ed",
    "source": "https://raw.githubusercontent.com/tiangolo/fastapi/master/README.md",
    "title": "FastAPI",
    "source_type": "url",
    "created_at": "2026-02-11T18:30:00Z",
    "chunk_count": 12
  },
  "chunks_created": 12
}
```

**Errors**

| Status | Condition                          |
|--------|------------------------------------|
| 422    | Missing or invalid `source` field  |
| 502    | Failed to load the source document |

---

## GET /documents

List all ingested documents.

**Response** `200`

```json
[
  {
    "id": "019c4dcd-428f-70e2-ad28-27e11a1c14ed",
    "source": "https://raw.githubusercontent.com/tiangolo/fastapi/master/README.md",
    "title": "FastAPI",
    "source_type": "url",
    "created_at": "2026-02-11T18:30:00Z",
    "chunk_count": 12
  }
]
```

---

## POST /ask

Ask a question about the ingested documentation.

**Request**

```json
{
  "question": "What is FastAPI?"
}
```

**Response** `200`

```json
{
  "text": "FastAPI is a modern, fast web framework for building APIs with Python based on standard Python type hints.",
  "sources": [
    {
      "document_title": "FastAPI",
      "chunk_text": "FastAPI is a modern, fast (high-performance), web framework...",
      "relevance_score": 0.92,
      "chunk_id": "019c4dce-1234-7890-abcd-ef0123456789"
    }
  ]
}
```

**Errors**

| Status | Condition                          |
|--------|------------------------------------|
| 422    | Missing or invalid `question` field|
| 502    | LLM or embedding service failure   |

---

## Error Format

All domain errors return a JSON body:

```json
{
  "detail": "Description of what went wrong"
}
```

| Status | Domain Exceptions                                          |
|--------|------------------------------------------------------------|
| 400    | `InvalidQuestionError`, `InvalidDocumentError`, `InvalidChunkError` |
| 404    | `DocumentNotFoundError`                                    |
| 502    | `DocumentLoadError`, `EmbeddingGenerationError`, `LLMGenerationError` |
