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

## POST /ingest/url

Ingest documentation from an HTTP or HTTPS URL.

**Request** `application/json`

| Field          | Type                              | Required | Default    | Description                                      |
|----------------|-----------------------------------|----------|------------|--------------------------------------------------|
| `source`       | string                            | yes      | —          | HTTP/HTTPS URL of the document to ingest         |
| `title`        | string \| null                    | no       | `null`     | Custom title; inferred from content if omitted   |
| `on_duplicate` | `"reject"` \| `"skip"` \| `"replace"` | no  | `"reject"` | Behaviour when a document with the same source already exists |
| `language`     | string                            | no       | `"english"`| Full-text search language for indexing           |

```json
{
  "source": "https://raw.githubusercontent.com/tiangolo/fastapi/master/README.md",
  "title": "FastAPI README",
  "on_duplicate": "skip",
  "language": "english"
}
```

**Response** `200`

```json
{
  "document": {
    "id": "019c4dcd-428f-70e2-ad28-27e11a1c14ed",
    "source": "https://raw.githubusercontent.com/tiangolo/fastapi/master/README.md",
    "title": "FastAPI README",
    "source_type": "url",
    "created_at": "2026-02-11T18:30:00Z",
    "chunk_count": 12,
    "language": "english"
  },
  "chunks_created": 12
}
```

**Errors**

| Status | Condition                                                            |
|--------|----------------------------------------------------------------------|
| 409    | Document with the same source already exists (`on_duplicate: "reject"`) |
| 422    | Missing or invalid field (non-HTTP URL, unsupported language, etc.)  |
| 502    | Failed to load the document from the given source                    |

---

## POST /ingest/file

Ingest documentation from an uploaded file.

**Request** `multipart/form-data`

| Field          | Type                              | Required | Default    | Description                                      |
|----------------|-----------------------------------|----------|------------|--------------------------------------------------|
| `file`         | file                              | yes      | —          | The file to upload                               |
| `title`        | string                            | no       | `null`     | Custom title; inferred from filename if omitted  |
| `on_duplicate` | `"reject"` \| `"skip"` \| `"replace"` | no  | `"reject"` | Behaviour when a document with the same content hash already exists |
| `language`     | string                            | no       | `"english"`| Full-text search language for indexing           |

The document source is derived from the SHA-256 hash of the file content (`sha256:<hex>`), so identical files are treated as duplicates regardless of filename.

Example with `curl`:

```bash
curl -X POST http://localhost:8000/ingest/file \
  -F "file=@./docs/guide.md" \
  -F "title=My Guide" \
  -F "on_duplicate=skip" \
  -F "language=english"
```

**Response** `200`

```json
{
  "document": {
    "id": "019c4dcd-428f-70e2-ad28-27e11a1c14ed",
    "source": "sha256:a3f1c2d...",
    "title": "My Guide",
    "source_type": "file",
    "created_at": "2026-02-11T18:30:00Z",
    "chunk_count": 8,
    "language": "english"
  },
  "chunks_created": 8
}
```

**Errors**

| Status | Condition                                                            |
|--------|----------------------------------------------------------------------|
| 409    | Document with the same content hash already exists (`on_duplicate: "reject"`) |
| 422    | Missing file, invalid field, or unsupported language                 |
| 502    | Failed to process the uploaded file                                  |

---

## GET /documents

List ingested documents with pagination.

**Query parameters**

| Parameter | Type    | Default | Description                   |
|-----------|---------|---------|-------------------------------|
| `offset`  | integer | `0`     | Number of documents to skip   |
| `limit`   | integer | `50`    | Maximum number of documents to return |

**Response** `200`

```json
[
  {
    "id": "019c4dcd-428f-70e2-ad28-27e11a1c14ed",
    "source": "https://raw.githubusercontent.com/tiangolo/fastapi/master/README.md",
    "title": "FastAPI README",
    "source_type": "url",
    "created_at": "2026-02-11T18:30:00Z",
    "chunk_count": 12,
    "language": "english"
  }
]
```

---

## POST /ask

Ask a question about the ingested documentation. Returns a complete response once generation finishes.

**Request** `application/json`

| Field      | Type    | Required | Description                                                |
|------------|---------|----------|------------------------------------------------------------|
| `question` | string  | yes      | The question to answer (1–1000 characters)                 |
| `history`  | array   | no       | Prior conversation turns for multi-turn context (max 50)   |

Each entry in `history` has:

| Field     | Type                    | Description                  |
|-----------|-------------------------|------------------------------|
| `role`    | `"user"` \| `"assistant"` | Who sent this message      |
| `content` | string                  | Message text (1–10000 chars) |

```json
{
  "question": "What is FastAPI?",
  "history": [
    { "role": "user", "content": "Tell me about Python web frameworks." },
    { "role": "assistant", "content": "There are several popular Python web frameworks..." }
  ]
}
```

**Response** `200`

```json
{
  "text": "FastAPI is a modern, fast web framework for building APIs with Python based on standard Python type hints.",
  "sources": [
    {
      "document_title": "FastAPI README",
      "chunk_text": "FastAPI is a modern, fast (high-performance), web framework...",
      "relevance_score": 0.92,
      "chunk_id": "019c4dce-1234-7890-abcd-ef0123456789"
    }
  ]
}
```

**Errors**

| Status | Condition                            |
|--------|--------------------------------------|
| 400    | Invalid question format              |
| 422    | Missing or invalid `question` field  |
| 502    | LLM or embedding service failure     |

---

## POST /ask/stream

Ask a question and receive the response as a stream of NDJSON events. Accepts the same request body as `POST /ask`.

**Request** `application/json`

Same fields as `POST /ask`.

**Response** `200` — `application/x-ndjson`

The response body is a sequence of newline-delimited JSON objects. Each line is one event. There are three event types emitted in order:

**`text` events** — one or more, carrying successive chunks of the generated answer:

```json
{"type": "text", "content": "FastAPI is a modern"}
{"type": "text", "content": ", fast web framework"}
```

**`sources` event** — exactly one, after all text events:

```json
{
  "type": "sources",
  "sources": [
    {
      "document_title": "FastAPI README",
      "chunk_text": "FastAPI is a modern, fast (high-performance), web framework...",
      "relevance_score": 0.92,
      "chunk_id": "019c4dce-1234-7890-abcd-ef0123456789"
    }
  ]
}
```

**`done` event** — exactly one, signals the stream is complete:

```json
{"type": "done"}
```

If no relevant chunks are found, the stream emits a single `text` event with a "no results" message, a `sources` event with an empty array, then `done`.

**Errors**

| Status | Condition                            |
|--------|--------------------------------------|
| 400    | Invalid question format              |
| 422    | Missing or invalid `question` field  |
| 502    | LLM or embedding service failure     |

---

## Error Format

All domain errors return a JSON body:

```json
{
  "detail": "Description of what went wrong"
}
```

| Status | Domain Exception(s)                                                          |
|--------|------------------------------------------------------------------------------|
| 400    | `InvalidQuestionError`, `InvalidDocumentError`, `InvalidChunkError`, `InvalidAnswerError` |
| 404    | `DocumentNotFoundError`                                                      |
| 409    | `DuplicateDocumentError`                                                     |
| 502    | `DocumentLoadError`, `EmbeddingGenerationError`, `LLMGenerationError`        |

502 responses use a sanitised message rather than the raw exception detail to avoid leaking internal state.
