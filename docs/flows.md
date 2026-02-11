# Flows

## Ingestion Flow

Triggered by `POST /ingest` with a source URL or file path.

```
                         ┌────────────────┐
                         │  POST /ingest  │
                         │  { source }    │
                         └───────┬────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │  DocumentLoaderService   │
                    │  Fetch URL or read file  │
                    └────────────┬─────────────┘
                                 │
                            raw content
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │  Split into chunks      │
                    │  ~500 words, 50 overlap │
                    └─────────────┬───────────┘
                                  │
                             text chunks[]
                                  │
                                  ▼
                    ┌─────────────────────┐
                    │  EmbeddingService   │
                    │  embed_batch(texts) │
                    └───────────┬─────────┘
                                │
                        chunks + embeddings
                                │
                ┌───────────────┴───────────────┐
                │                               │
                ▼                               ▼
    ┌──────────────────────┐      ┌───────────────────┐
    │  DocumentRepository  │      │  ChunkRepository  │
    │  save(document)      │      │  save_all(chunks) │
    └──────────────────────┘      └───────────────────┘
          ▲ saved first                 ▲ saved second
          │                             │
          └──────────────┬──────────────┘
                         │
                         ▼
               ┌────────────────────┐
               │  IngestResultDTO   │
               │  document + count  │
               └────────────────────┘
```

**Key detail**: The document is saved before the chunks because of the foreign key constraint (`chunks.document_id → documents.id`).

---

## Ask Question Flow

Triggered by `POST /ask` with a question.

```
                         ┌────────────────┐
                         │  POST /ask     │
                         │  { question }  │
                         └───────┬────────┘
                                 │
                                 ▼
                    ┌───────────────────────────┐
                    │  Validate question        │
                    │  (non-empty, ≤1000 chars) │
                    └───────────────┬───────────┘
                                    │
                                    ▼
                    ┌────────────────────┐
                    │  EmbeddingService  │
                    │  embed(question)   │
                    └───────────┬────────┘
                                │
                       question embedding
                                │
                                ▼
                    ┌──────────────────────────┐
                    │  ChunkRepository         │
                    │  search_similar(         │
                    │    embedding, top_k=5)   │
                    └────────────┬─────────────┘
                                 │
                    top-k chunks + scores
                                 │
                ┌────────────────┴────────────────┐
                │                                 │
                ▼                                 ▼
    ┌──────────────────────┐      ┌──────────────────────┐
    │  LLMService          │      │  DocumentRepository  │
    │  generate(question,  │      │  find_by_id()        │
    │    context_chunks)   │      │  (resolve titles)    │
    └──────────┬───────────┘      └──────────┬───────────┘
               │                             │
         answer text                  document titles
               │                             │
               └──────────────┬──────────────┘
                              │
                              ▼
                    ┌──────────────────────────┐
                    │  Build AnswerDTO         │
                    │  text + sources with     │
                    │  titles and scores       │
                    └──────────────────────────┘
```

The LLM generates the answer text. Source references (with document titles and relevance scores) are built by the use case, not the LLM service.
