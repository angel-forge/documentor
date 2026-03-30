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

| Component              | Type            | Description                                     |
|------------------------|-----------------|-------------------------------------------------|
| `Document`             | Entity          | Metadata for an ingested source                 |
| `Chunk`                | Entity          | Text fragment with optional embedding           |
| `Question`             | Value Object    | Validated user question (max 1000 chars)        |
| `Answer`               | Value Object    | Generated text with source references           |
| `SourceReference`      | Value Object    | Single source citation with relevance score     |
| `Embedding`            | Value Object    | Immutable vector representation of text         |
| `ChunkContent`         | Value Object    | Text fragment paired with its token count       |
| `ConversationMessage`  | Value Object    | Single turn in a conversation (role + content)  |
| `SourceType`           | Enum            | `url`, `file`, or `text`                        |
| `DocumentRepository`   | Port (ABC)      | Persistence for documents                       |
| `ChunkRepository`      | Port (ABC)      | Persistence, vector search, and hybrid search   |
| `LLMService`           | Port (ABC)      | Text generation, streaming, and query rewriting |
| `EmbeddingService`     | Port (ABC)      | Embedding generation (single and batch)         |
| `DocumentLoaderService`| Port (ABC)      | Content fetching (URL or file)                  |

#### `ChunkRepository` port methods

| Method             | Description                                              |
|--------------------|----------------------------------------------------------|
| `save_all`         | Persist a list of chunks                                 |
| `search_similar`   | ANN vector search returning `(Chunk, score)` pairs      |
| `search_hybrid`    | Hybrid ANN + full-text search with RRF score fusion      |
| `delete_by_document_id` | Remove all chunks belonging to a document           |

#### `LLMService` port methods

| Method           | Description                                           |
|------------------|-------------------------------------------------------|
| `generate`       | Generate an answer from question + context chunks     |
| `generate_stream`| Same as `generate` but returns an `AsyncIterator[str]`|
| `rewrite_query`  | Rewrite a follow-up question given conversation history|

### Application

| Use Case               | Description                                                              |
|------------------------|--------------------------------------------------------------------------|
| `IngestDocumentation`  | Load → chunk → embed → store; supports duplicate handling policies       |
| `AskQuestion`          | Rewrite query (if history) → embed → hybrid search → generate → return   |
| `ListDocuments`        | Return ingested documents with offset/limit pagination                   |

`AskQuestion` exposes two execution paths:
- `execute` — returns a fully resolved `AnswerDTO`
- `execute_stream` — yields NDJSON events (`text`, `sources`, `done`)

### Infrastructure

#### Persistence

| Implementation            | Implements              | Notes                                   |
|---------------------------|-------------------------|-----------------------------------------|
| `PgDocumentRepository`    | `DocumentRepository`    | SQLAlchemy 2.0, async                   |
| `PgChunkRepository`       | `ChunkRepository`       | pgvector ANN + PostgreSQL FTS with RRF  |
| `PgUnitOfWork`            | `UnitOfWork`            | Manages `AsyncSession` and transaction  |

#### External services

| Implementation            | Implements              | Notes                                              |
|---------------------------|-------------------------|----------------------------------------------------|
| `OpenAIEmbeddingService`  | `EmbeddingService`      | `text-embedding-3-small`; tiktoken token counting  |
| `AnthropicLLMService`     | `LLMService`            | `claude-sonnet-4-5`; separate rewrite model        |
| `OpenAILLMService`        | `LLMService`            | `gpt-4o-mini`; alternative LLM backend             |
| `HttpDocumentLoader`      | `DocumentLoaderService` | Fetches URLs; SSRF protection via IP validation    |
| `FileDocumentLoader`      | `DocumentLoaderService` | Reads uploaded files; supports PDF, MD, TXT, HTML  |

#### Observability

| Wrapper                   | Wraps               | Notes                                        |
|---------------------------|---------------------|----------------------------------------------|
| `ObservedLLMService`      | `LLMService`        | Decorator; traces generate/stream/rewrite via Langfuse |
| `ObservedEmbeddingService`| `EmbeddingService`  | Decorator; traces embed/embed_batch via Langfuse       |

Both observability wrappers implement the same port interface as their inner service and are transparent to callers. They are composed in `dependencies.py` when Langfuse is configured.

#### Prompt construction

| Component      | Description                                                     |
|----------------|-----------------------------------------------------------------|
| `PromptBuilder`| Functions for RAG system prompt, query rewrite prompt, and rewrite user message (`build_rag_system_prompt`, `build_query_rewrite_prompt`, `build_rewrite_user_message`) |

### Adapters

| Endpoint        | Method | Description                                  |
|-----------------|--------|----------------------------------------------|
| `/health`       | GET    | Health check                                 |
| `/ingest/url`   | POST   | Ingest documentation from a URL             |
| `/ingest/file`  | POST   | Ingest documentation from an uploaded file  |
| `/documents`    | GET    | List ingested documents (pagination via `offset`/`limit`) |
| `/ask`          | POST   | Ask a question; returns full `AnswerResponse`|
| `/ask/stream`   | POST   | Ask a question; streams NDJSON events        |
