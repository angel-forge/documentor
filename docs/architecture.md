# Architecture Overview

DocuMentor follows Hexagonal Architecture (Ports & Adapters) with DDD tactical patterns.

## Layers

```
┌─────────────────────────────────────────────┐
│  adapters/api/                              │
│  FastAPI routes, schemas, DI, error handlers│
├─────────────────────────────────────────────┤
│  application/                               │
│  Use cases (IngestDocumentation, AskQuestion│
│  ListDocuments) and DTOs                    │
├─────────────────────────────────────────────┤
│  domain/                                    │
│  Entities, Value Objects, port interfaces   │
├─────────────────────────────────────────────┤
│  infrastructure/                            │
│  PostgreSQL repos, OpenAI, Anthropic, HTTP  │
└─────────────────────────────────────────────┘
```

## Dependency Flow

```
adapters  ──→  application  ──→  domain  ←──  infrastructure
```

- `domain/` imports nothing from other layers.
- `application/` imports only from `domain/`.
- `infrastructure/` imports from `domain/` (implements port interfaces).
- `adapters/` imports from `application/` and `domain/`. The DI container (`dependencies.py`) is the only adapter file that touches `infrastructure/`.

## Key Components

### Domain

| Component              | Type            | Description                          |
|------------------------|-----------------|--------------------------------------|
| `Document`             | Entity          | Metadata for an ingested source      |
| `Chunk`                | Entity          | Text fragment with embedding         |
| `Question`             | Value Object    | Validated user question              |
| `Answer`               | Value Object    | Generated text with source refs      |
| `Embedding`            | Value Object    | Vector representation of text        |
| `DocumentRepository`   | Port (ABC)      | Persistence for documents            |
| `ChunkRepository`      | Port (ABC)      | Persistence + vector search          |
| `LLMService`           | Port (ABC)      | Text generation                      |
| `EmbeddingService`     | Port (ABC)      | Embedding generation                 |
| `DocumentLoaderService`| Port (ABC)      | Content fetching (URL/file)          |

### Application

| Use Case               | Description                                       |
|-------------------------|---------------------------------------------------|
| `IngestDocumentation`   | Load → chunk → embed → store                      |
| `AskQuestion`           | Embed question → search → generate → return answer |
| `ListDocuments`         | Return all ingested documents                      |

### Infrastructure

| Implementation            | Implements              |
|---------------------------|-------------------------|
| `PgDocumentRepository`    | `DocumentRepository`    |
| `PgChunkRepository`       | `ChunkRepository`       |
| `OpenAILLMService`        | `LLMService`            |
| `AnthropicLLMService`     | `LLMService`            |
| `OpenAIEmbeddingService`  | `EmbeddingService`      |
| `HttpDocumentLoader`      | `DocumentLoaderService` |

### Adapters

| Endpoint         | Method | Description                      |
|------------------|--------|----------------------------------|
| `/health`        | GET    | Health check                     |
| `/ingest`        | POST   | Ingest documentation from source |
| `/documents`     | GET    | List ingested documents          |
| `/ask`           | POST   | Ask a question                   |
