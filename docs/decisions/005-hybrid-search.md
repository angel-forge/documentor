# 005 — Hybrid Search

Date: 2026-03-30

## Context

The system relied on pure vector similarity search (pgvector cosine distance) for retrieving relevant chunks. While effective for semantic matching, vector search performs poorly on exact keyword lookups — function names, error codes, configuration flags, and other precise technical terms that users frequently search for in documentation.

## Decision

Combine vector similarity search with PostgreSQL full-text search (tsvector/GIN), merging results via Reciprocal Rank Fusion (RRF). Both searches run against the same PostgreSQL database with no additional infrastructure.

## How It Works

1. **Vector search**: Existing pgvector cosine similarity via HNSW index. Returns candidates ranked by semantic similarity.
2. **Full-text search**: PostgreSQL `plainto_tsquery` + `ts_rank_cd` against a `tsvector` column with a GIN index. Returns candidates ranked by lexical relevance.
3. **RRF fusion**: Both result sets (each `top_k * 2` candidates) are merged using `RRF_score(d) = Σ 1/(k + rank_i)`, then normalized to `[0, 1]` by dividing by the theoretical maximum `num_lists / (k + 1)`.

## Key Decisions

### RRF in Python, not SQL

Two separate queries + Python fusion rather than a single combined SQL CTE. Each query is simple, independently testable, and hits its own index. The RRF function is a pure function with no database dependency.

### Normalized scores

RRF raw scores have a different distribution than cosine similarity. Rather than recalibrating thresholds, scores are normalized to `[0, 1]`, preserving the existing `MIN_RELEVANCE_SCORE = 0.3` threshold.

### New port method

`search_hybrid` was added as a new method on `ChunkRepository` rather than modifying `search_similar`. Different signature (requires `query_text` and `language`), and keeping both methods makes rollback trivial.

### Configurable parameters

- `SEARCH_LANGUAGE` (default `english`) — PostgreSQL FTS configuration for `plainto_tsquery`.
- `RRF_K` (default `60`) — RRF constant from the original paper. Controls how much rank position matters.

## Consequences

- Two database round-trips per search instead of one. Acceptable at current scale.
- FTS handles code symbols imperfectly (underscores split tokens, CamelCase lowercased). Vector search compensates.
- The `search_vector` column adds storage overhead (~2-5x the text size as tsvector), negligible for documentation chunks.

## What We Avoided

- **Single combined SQL query**: Awkward with window functions and CTEs, harder to debug ranking issues.
- **External search engine** (Elasticsearch, Meilisearch): Unnecessary infrastructure for current scale.
- **Concurrent queries via asyncio.gather**: YAGNI — sequential queries are fast enough.
