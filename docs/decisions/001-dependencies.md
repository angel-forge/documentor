# 001 — Dependencies

Date: 2026-02-11
Updated: 2026-02-15

## Production Dependencies

### fastapi
Web framework for building the REST API. Chosen for its async support, automatic OpenAPI docs generation, and native Pydantic integration for request/response validation.

### uvicorn
ASGI server to run the FastAPI application. Lightweight and performant, supports hot reload during development.

### sqlalchemy
ORM and database toolkit (v2.0+ with modern `mapped_column` style). Provides the data access layer for PostgreSQL, used in the infrastructure layer to implement domain repository interfaces.

### asyncpg
Async PostgreSQL driver. Required by SQLAlchemy for async database operations, which align with FastAPI's async nature.

### alembic
Database migration tool built on top of SQLAlchemy. Every schema change gets a versioned migration file, enabling reproducible and reversible database evolution.

### pgvector
SQLAlchemy extension for the `pgvector` PostgreSQL extension. Provides the `Vector` column type for storing and querying embeddings, which is the core of the RAG retrieval mechanism.

### pydantic-settings
Configuration management via environment variables and `.env` files. Ensures no API keys, database URLs, or model parameters are hardcoded.

### anthropic
Official Anthropic SDK for interacting with Claude. Used in the infrastructure layer as one of the LLM service implementations for answer generation, streaming, and query rewriting.

### openai
Official OpenAI SDK. Used for the embedding service (`text-embedding-3-small`) and as an alternative LLM provider for answer generation.

### httpx
Async HTTP client. Used for fetching remote documentation during the ingestion pipeline (`HttpDocumentLoader` implementation).

### tiktoken
OpenAI's tokenizer library. Used by `OpenAIEmbeddingService` to count tokens per chunk during ingestion, which is stored as metadata on each `Chunk`.

### langfuse
LLM observability platform SDK. Used in the infrastructure layer to trace LLM calls, embeddings, and query rewrites via the wrapper pattern (`ObservedLLMService`, `ObservedEmbeddingService`). Opt-in via `LANGFUSE_ENABLED` — zero overhead when disabled.

### pymupdf
PDF content extraction library. Used by `FileDocumentLoader` to extract text from uploaded PDF files during ingestion.

### python-multipart
Required by FastAPI for parsing `multipart/form-data` requests. Enables the file upload endpoint (`POST /ingest/file`).

### uuid-utils
Provides UUID7 generation for entity IDs. UUID7 is time-ordered, which gives better database index locality than random UUID4.

## Dev Dependencies

### pytest
Testing framework. Chosen for its fixture system, parametrize support, and extensive plugin ecosystem.

### pytest-asyncio
Pytest plugin for testing async code. Required because both FastAPI endpoints and database operations are async.

### pytest-cov
Coverage reporting plugin for pytest. Used to enforce the 90% coverage target on domain + application layers.

### ruff
Linter and formatter (replaces flake8, isort, black). Single tool for both `ruff check` and `ruff format`, fast and configured via `pyproject.toml`.

### testcontainers
Spins up real PostgreSQL + pgvector Docker containers for integration tests. Ensures tests run against the actual database engine, not SQLite mocks.

### httpx (dev)
Also listed as dev dependency because `httpx.AsyncClient` is used as the test client for FastAPI e2e tests (replaces `requests` in async contexts).

### greenlet
Required by SQLAlchemy for async operations in certain contexts. Listed explicitly to avoid implicit dependency resolution issues.

### rich
Terminal formatting library. Used for development tooling and test output readability.
