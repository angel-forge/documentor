# 003 — RAG Strategy

Date: 2026-02-11
Updated: 2026-02-15

## Context

DocuMentor answers questions about public technical documentation. The system needs to retrieve relevant content and provide grounded answers with source references. It also supports multi-turn conversations where follow-up questions may reference prior context.

## Decision

Implement a conversational RAG (Retrieval-Augmented Generation) pipeline with vector similarity search via pgvector, query rewriting for multi-turn context, and streaming answer generation.

## Ingestion Pipeline

1. **Load** — Fetch content from a URL (`HttpDocumentLoader`) or extract from an uploaded file (`FileDocumentLoader`). Supported file formats: `.txt`, `.md`, `.html`, `.rst`, `.pdf`. PDF extraction uses PyMuPDF. File uploads are validated for extension, size (10 MB max), and content (magic bytes for PDF, UTF-8 for text).
2. **Chunk** — Split text into ~500-word chunks with ~50-word overlap. Word-boundary splitting (no mid-sentence cuts).
3. **Embed** — Generate embeddings for each chunk using OpenAI's `text-embedding-3-small` (1536 dimensions). Token count is stored per chunk as metadata.
4. **Store** — Save the document metadata and chunks with embeddings to PostgreSQL + pgvector, atomically via Unit of Work.

Duplicate detection is built in — re-ingesting an existing source can be rejected, skipped, or replaced (old document + chunks deleted, then re-ingested).

## Query Pipeline

1. **Rewrite** (conditional) — If the conversation has history, a lightweight LLM rewrites the follow-up question into a standalone search query. First-turn questions skip this step entirely. See [Query Rewriting](#query-rewriting) below.
2. **Embed** — Generate an embedding for the search query (rewritten or original).
3. **Search** — Cosine similarity search via pgvector, returning top-k (default 5) most relevant chunks. Results below a minimum relevance score (0.3) are filtered out.
4. **Generate** — Pass the question, conversation history, and retrieved chunks to the LLM with a system prompt that constrains answers to the provided context.
5. **Return** — Answer text + source references with document titles and relevance scores.

Both synchronous (`POST /ask`) and streaming (`POST /ask/stream`) endpoints are available. The streaming variant returns NDJSON chunks: incremental text tokens as they're generated, followed by a sources payload and a done signal.

## Query Rewriting

In multi-turn conversations, follow-up questions are often ambiguous without prior context (e.g., "what about performance?" or "can you name a few people involved?"). Embedding the raw question would retrieve irrelevant chunks.

When conversation history is present, the `AskQuestion` use case calls `LLMService.rewrite_query()` to transform the follow-up into a standalone query. The rewrite step:

- Uses a dedicated system prompt instructing the model to output only the rewritten query.
- Truncates conversation history to the last 10 messages / 2,000 characters to bound cost and latency.
- Runs on a fast, cheap model (e.g., Claude Haiku, GPT-4o-mini) — separate from the main generation model.
- Falls back to the original question text if rewriting fails for any reason.

## Chunking Strategy

- **Fixed word count** (~500 words) with overlap (~50 words) rather than semantic splitting.
- Overlap ensures context isn't lost at chunk boundaries.
- Simple and deterministic. Semantic splitting (by headings, paragraphs) can be added later if needed.

## Why pgvector

- PostgreSQL is already the primary datastore. pgvector avoids a separate vector database (Pinecone, Qdrant, etc.).
- Cosine distance is native and indexed. Sufficient for the expected document volume.
- Fewer moving parts in development and deployment.

## Embedding Model

- `text-embedding-3-small` chosen for cost-efficiency and good quality at 1536 dimensions.
- Configurable via `EMBEDDING_MODEL` and `EMBEDDING_DIMENSION` environment variables.

## What We Avoided

- **Re-ranking**: Not implemented. Top-k cosine similarity with a minimum score threshold is sufficient for now.
- **Hybrid search** (keyword + vector): Not needed until retrieval quality proves insufficient.
- **Chunk metadata enrichment** (headers, hierarchy): Chunks store raw text only. Can be added if context quality is an issue.
