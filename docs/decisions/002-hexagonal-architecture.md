# 002 — Hexagonal Architecture + DDD

Date: 2026-02-11

## Context

DocuMentor is a RAG application that combines multiple external systems: a database with vector search, embedding APIs, LLM APIs, and HTTP fetching. The business logic (chunking, orchestration, validation) needs to remain testable and independent from these external systems.

## Decision

Adopt Hexagonal Architecture (Ports & Adapters) combined with lightweight DDD tactical patterns.

## Structure

```
src/documentor/
├── domain/            # Entities, Value Objects, port interfaces
├── application/       # Use cases and DTOs
├── infrastructure/    # Port implementations (DB, APIs, HTTP)
└── adapters/          # Primary adapter (FastAPI API)
```

## Dependency Rules

1. **`domain/`** imports nothing from other layers. Zero external dependencies.
2. **`application/`** imports only from `domain/`. Never from `infrastructure/` or `adapters/`.
3. **`infrastructure/`** imports from `domain/` to implement port interfaces.
4. **`adapters/`** imports from `application/` and `domain/`. The DI container (`dependencies.py`) is the single file that touches `infrastructure/`.

## DDD Patterns Used

- **Entities**: `Document`, `Chunk` — have identity (`id`) and lifecycle.
- **Value Objects**: `Question`, `Embedding`, `ChunkContent`, `Answer`, `SourceReference` — immutable, compared by value, use `@dataclass(frozen=True)`.
- **Repository interfaces**: `DocumentRepository`, `ChunkRepository` — defined as ABCs in domain, implemented in infrastructure.
- **Service interfaces**: `LLMService`, `EmbeddingService`, `DocumentLoaderService` — same pattern as repositories.
- **Unit of Work**: `UnitOfWork` — defined as an ABC in domain, implemented as `PgUnitOfWork` in infrastructure. Manages a shared session across repositories and controls transaction boundaries (`commit`/`rollback`).

## Why Not Simpler

A flat FastAPI app with SQLAlchemy models directly in the route handlers would work for a prototype. Hexagonal was chosen because:

- **Testability**: Use cases are tested with mocks for all external services. Domain logic is tested with zero mocks.
- **Swappability**: LLM provider (OpenAI/Anthropic) is swapped via configuration, not code changes.
- **Clarity**: Each layer has a single responsibility and a clear API boundary.

## What We Avoided

- **Aggregates**: Not needed yet. `Document` and `Chunk` are related but transactional consistency is handled by the `UnitOfWork` pattern rather than an aggregate root.
- **Domain Events**: Not needed. The ingestion pipeline is a straightforward sequential flow.
- **CQRS**: Single model for reads and writes is sufficient at this scale.
