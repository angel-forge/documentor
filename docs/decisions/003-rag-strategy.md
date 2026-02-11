# 003 — RAG Strategy

Date: 2026-02-11

## Context

DocuMentor answers questions about public technical documentation. The system needs to retrieve relevant content and provide grounded answers with source references.

## Decision

Implement a standard RAG (Retrieval-Augmented Generation) pipeline with vector similarity search via pgvector.

## Ingestion Pipeline

1. **Load** — Fetch content from a URL or read from a local file path.
2. **Chunk** — Split text into ~500-word chunks with ~50-word overlap. Word-boundary splitting (no mid-sentence cuts).
3. **Embed** — Generate embeddings for each chunk using OpenAI's `text-embedding-3-small` (1536 dimensions).
4. **Store** — Save the document metadata and chunks with embeddings to PostgreSQL + pgvector.

## Query Pipeline

1. **Embed** — Generate an embedding for the user's question.
2. **Search** — Cosine similarity search via pgvector, returning top-k (default 5) most relevant chunks.
3. **Generate** — Pass the question and retrieved chunks to the LLM with a system prompt that constrains answers to the provided context.
4. **Return** — Answer text + source references with document titles and relevance scores.

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

- **Re-ranking**: Not implemented. Top-k cosine similarity is sufficient for now.
- **Hybrid search** (keyword + vector): Not needed until retrieval quality proves insufficient.
- **Chunk metadata enrichment** (headers, hierarchy): Chunks store raw text only. Can be added if context quality is an issue.
