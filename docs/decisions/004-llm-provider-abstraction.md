# 004 — LLM Provider Abstraction

Date: 2026-02-11
Updated: 2026-02-15

## Context

The system uses an LLM to generate answers from retrieved context, stream responses token-by-token, and rewrite conversational follow-ups into standalone search queries. We want to support multiple LLM providers without coupling the application logic to any specific one.

## Decision

Define `LLMService` as a domain port (abstract interface) with concrete implementations in the infrastructure layer. Provider selection happens at dependency injection time based on configuration.

## Interface

```python
class LLMService(ABC):
    @abstractmethod
    async def generate(
        self,
        question: Question,
        context_chunks: list[Chunk],
        conversation_history: tuple[ConversationMessage, ...] = (),
    ) -> str: ...

    @abstractmethod
    def generate_stream(
        self,
        question: Question,
        context_chunks: list[Chunk],
        conversation_history: tuple[ConversationMessage, ...] = (),
    ) -> AsyncIterator[str]: ...

    @abstractmethod
    async def rewrite_query(
        self,
        question: Question,
        conversation_history: tuple[ConversationMessage, ...],
    ) -> str: ...
```

Three responsibilities:

- **`generate()`** — Single-shot answer generation with full conversation context. Returns the complete answer text.
- **`generate_stream()`** — Same as `generate()` but yields text tokens incrementally via `AsyncIterator`. Used by the `/ask/stream` endpoint for real-time UX.
- **`rewrite_query()`** — Takes a follow-up question and conversation history, returns a standalone search query. Only called when history is present (the `AskQuestion` use case handles this conditional logic).

The LLM service does **not** build source references — that responsibility belongs to the `AskQuestion` use case, which has access to document metadata via the repository.

## Implementations

| Provider   | Class                  | Config value              |
|------------|------------------------|---------------------------|
| OpenAI     | `OpenAILLMService`     | `LLM_PROVIDER=openai`    |
| Anthropic  | `AnthropicLLMService`  | `LLM_PROVIDER=anthropic` |

Both implementations:

- Share the same prompt structure via `prompt_builder.py` — context chunks are formatted with source identifiers, and the LLM is instructed to answer only from the provided context.
- Support a separate `rewrite_model` for query rewriting, allowing a fast/cheap model for rewrites while using a more capable model for answer generation.
- Convert conversation history into the provider's native message format.

## Observability

When `LANGFUSE_ENABLED=true`, the DI container wraps the LLM service in `ObservedLLMService` — a decorator that traces every call to Langfuse without modifying the underlying service. The same pattern applies to the embedding service via `ObservedEmbeddingService`.

Traced operations:

| Trace name | Method | What it logs |
|------------|--------|--------------|
| `llm-generate` | `generate()` | Question, history, context chunks, full output |
| `llm-generate-stream` | `generate_stream()` | Question, history, context chunks, collected streamed output |
| `llm-rewrite-query` | `rewrite_query()` | Question, history, rewritten query |
| `embedding-embed` | `embed()` | Input text snippet, output dimension |
| `embedding-embed-batch` | `embed_batch()` | Batch count |

When `LANGFUSE_ENABLED=false` (the default), the wrappers are not applied and there is zero performance overhead.

## Configuration

Controlled via environment variables:

- `LLM_PROVIDER` — `"openai"` (default) or `"anthropic"`
- `LLM_MODEL` — model identifier for answer generation (e.g., `"gpt-4o-mini"`, `"claude-sonnet-4-5-20250929"`)
- `LLM_REWRITE_MODEL` — model identifier for query rewriting (e.g., `"gpt-4o-mini"`, `"claude-haiku-4-5-20251001"`)
- `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` — provider credentials
- `LANGFUSE_ENABLED`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST` — observability config

## Why the LLM Doesn't Build Sources

Source references require document titles, which the LLM service doesn't have access to (chunks only carry `document_id`). The `AskQuestion` use case resolves titles via `DocumentRepository.find_by_ids()` and builds the source list using the actual similarity scores from the vector search. This keeps the LLM service focused on text generation.

## Error Handling

Both implementations catch provider-specific exceptions and wrap them in `LLMGenerationError` (a domain exception), which the error handler maps to HTTP 502. Query rewriting has an additional safety net: if the rewrite fails, the use case falls back to the original question text rather than failing the entire request.
