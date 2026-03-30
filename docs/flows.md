# Flows

## Ingestion Flow

Triggered by `POST /ingest` with a source URL or file path and optional `language` and `title` parameters.

```
                         ┌──────────────────────────────┐
                         │  POST /ingest                │
                         │  { source, language, title } │
                         └──────────────┬───────────────┘
                                        │
                                        ▼
                         ┌──────────────────────────┐
                         │  Duplicate check         │
                         │  find_by_source(source)  │
                         │                          │
                         │  on_duplicate:           │
                         │    reject → raise error  │
                         │    skip   → return early │
                         │    replace → delete old  │
                         └──────────────┬───────────┘
                                        │
                                        ▼
                         ┌──────────────────────────┐
                         │  DocumentLoaderService   │
                         │  load(source)            │
                         │  (fetch URL or read file)│
                         └──────────────┬───────────┘
                                        │
                                   raw content
                                        │
                                        ▼
                         ┌──────────────────────────────────────┐
                         │  split_text_into_chunks(             │
                         │    content,                          │
                         │    token_counter=embed.count_tokens) │
                         │                                      │
                         │  Structure-aware markdown path       │
                         │  (when ATX headings detected):       │
                         │    1. Parse into sections via        │
                         │       line-by-line state machine     │
                         │       (code fences preserved as      │
                         │       atomic units)                  │
                         │    2. Merge adjacent small sections  │
                         │       greedily up to chunk_size      │
                         │    3. Split large sections:          │
                         │       paragraph → line → word        │
                         │    4. Prepend heading context chain  │
                         │       to each output chunk           │
                         │                                      │
                         │  Plain text fallback path            │
                         │  (no headings detected):             │
                         │    word-boundary split               │
                         │    (~500 tokens, 50 token overlap)   │
                         └──────────────────────────────────────┘
                                        │
                                   text chunks[]
                                        │
                                        ▼
                         ┌──────────────────────────────┐
                         │  EmbeddingService            │
                         │  count_tokens(chunk) → each  │
                         │  embed_batch(texts) → all    │
                         └──────────────┬───────────────┘
                                        │
                                chunks + embeddings
                                        │
                    ┌───────────────────┴───────────────────┐
                    │                                       │
                    ▼                                       ▼
        ┌───────────────────────┐           ┌──────────────────────────┐
        │  DocumentRepository   │           │  ChunkRepository         │
        │  save(document)       │           │  save_all(chunks)        │
        │  (saved first — FK    │           │  (flush → tsvector       │
        │   constraint)         │           │   trigger auto-populates │
        └───────────────────────┘           │   search_vector)         │
                                            └──────────────────────────┘
                    │                                       │
                    └──────────────────┬────────────────────┘
                                       │
                                  uow.commit()
                                       │
                                       ▼
                              ┌─────────────────────┐
                              │  IngestResultDTO     │
                              │  document + count    │
                              └─────────────────────┘
```

**Key details**:
- The document is saved before the chunks because of the foreign key constraint (`chunks.document_id → documents.id`).
- `token_counter` is the embedding service's `count_tokens` method, passed into `split_text_into_chunks` so chunk sizes are measured in tokens rather than words.
- The `search_vector` (tsvector) column is populated automatically by a PostgreSQL trigger on insert — no explicit application-level call required.
- `language` is stored on both the document and each chunk; it controls the tsvector configuration used by the FTS trigger and at query time.
- The heading context chain (e.g., `# API Reference\n### Authentication\n`) is prepended to each chunk body so retrieval has structural context even without the surrounding document.

---

## Ask Question Flow

Triggered by `POST /ask` (blocking) or `POST /ask/stream` (SSE streaming). Both paths share the same retrieval logic; they diverge only at LLM generation.

### Non-streaming (`execute`)

```
                         ┌────────────────────────────────┐
                         │  POST /ask                     │
                         │  { question, history? }        │
                         └──────────────┬─────────────────┘
                                        │
                                        ▼
                         ┌──────────────────────────────────┐
                         │  Validate question               │
                         │  (non-empty, ≤ 1000 chars)       │
                         └──────────────┬───────────────────┘
                                        │
                                        ▼
                         ┌──────────────────────────────────┐
                         │  Query rewrite (conditional)     │
                         │                                  │
                         │  if history is not empty:        │
                         │    LLMService.rewrite_query(     │
                         │      question, history)          │
                         │    → standalone search query     │
                         │                                  │
                         │  else:                           │
                         │    use original question text    │
                         └──────────────┬───────────────────┘
                                        │
                                  search_query (str)
                                        │
                                        ▼
                         ┌──────────────────────────┐
                         │  EmbeddingService        │
                         │  embed(search_query)     │
                         └──────────────┬───────────┘
                                        │
                                  query embedding
                                        │
                                        ▼
                         ┌──────────────────────────────────────────┐
                         │  ChunkRepository.search_hybrid(          │
                         │    embedding, search_query,              │
                         │    top_k=5, language)                    │
                         │                                          │
                         │  Internally:                             │
                         │    candidate_count = top_k * 2 = 10      │
                         │                                          │
                         │    [A] vector search (cosine similarity) │
                         │        → top 10 (chunk_id, chunk, score) │
                         │                                          │
                         │    [B] FTS search (plainto_tsquery       │
                         │        + ts_rank_cd on search_vector)    │
                         │        → top 10 (chunk_id, chunk, score) │
                         │        (skipped if query is empty or     │
                         │         all stop words)                  │
                         │                                          │
                         │    [C] Reciprocal Rank Fusion (RRF)      │
                         │        score(chunk) = Σ 1/(k + rank_i)   │
                         │        k = 60 (default)                  │
                         │        normalized to [0, 1]:             │
                         │          score / (num_lists / (k+1))     │
                         │        → top 5 by normalized RRF score   │
                         └──────────────┬───────────────────────────┘
                                        │
                                top-5 (chunk, rrf_score)
                                        │
                                        ▼
                         ┌──────────────────────────────────┐
                         │  Filter: score >= MIN_HYBRID_SCORE│
                         │  (threshold = 0.3)               │
                         │                                  │
                         │  if no results:                  │
                         │    return "No relevant docs"     │
                         └──────────────┬───────────────────┘
                                        │
                                filtered chunks
                                        │
                    ┌───────────────────┴────────────────────┐
                    │                                        │
                    ▼                                        ▼
        ┌───────────────────────┐            ┌──────────────────────────┐
        │  LLMService           │            │  DocumentRepository      │
        │  generate(            │            │  find_by_ids(doc_ids)    │
        │    question, chunks,  │            │  (resolve titles)        │
        │    history)           │            └──────────────┬───────────┘
        └───────────┬───────────┘                           │
                    │                                document titles
               answer text                                  │
                    │                                       │
                    └──────────────────┬────────────────────┘
                                       │
                                       ▼
                         ┌──────────────────────────────────┐
                         │  Build AnswerDTO                  │
                         │  text + SourceReference[]        │
                         │  (title, chunk_text, score,      │
                         │   chunk_id per source)           │
                         └──────────────────────────────────┘
```

### Streaming (`execute_stream`)

The streaming path follows the same retrieval steps (query rewrite → embed → `search_hybrid` → score filter). The divergence happens after filtering:

```
              filtered chunks
                    │
                    ▼
    ┌───────────────────────────────────────┐
    │  DocumentRepository.find_by_ids()     │
    │  (resolved before streaming starts)   │
    └──────────────────────────────────────┘
                    │
                    ▼
    ┌───────────────────────────────────────┐
    │  LLMService.generate_stream(          │
    │    question, chunks, history)         │
    │                                       │
    │  yields SSE events:                   │
    │    { type: "text", content: "..." }   │  ← one per token/delta
    │    { type: "text", content: "..." }   │
    │    ...                                │
    └──────────────────────────────────────┘
                    │
                    ▼
    ┌───────────────────────────────────────┐
    │  After stream completes:              │
    │    { type: "sources", sources: [...] }│
    │    { type: "done" }                   │
    └──────────────────────────────────────┘
```

**Key details**:
- Query rewrite is always an LLM call, but only fires when `conversation_history` is non-empty. The rewrite produces a concise standalone query optimized for semantic search (last 10 messages, capped at 2000 chars of history).
- Hybrid search fetches `top_k * 2` candidates from each subsystem before RRF, widening the candidate pool so both signals can contribute.
- RRF normalization: maximum achievable score is `num_lists / (k + 1)`. With two lists and k=60, a chunk ranked #1 in both gets a normalized score of 1.0.
- The `MIN_HYBRID_SCORE = 0.3` threshold acts as a noise floor; chunks with insufficient combined signal are discarded before LLM generation.
- Source references (document titles, relevance scores) are assembled by the use case, not by the LLM service.
- The RAG system prompt injects each chunk as `[Source N | chunk_id=... | document_id=...]` followed by the chunk text, so the model can cite sources precisely.
