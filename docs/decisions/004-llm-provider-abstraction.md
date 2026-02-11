# 004 — LLM Provider Abstraction

Date: 2026-02-11

## Context

The system uses an LLM to generate answers from retrieved context. We want to support multiple LLM providers without coupling the application logic to any specific one.

## Decision

Define `LLMService` as a domain port (abstract interface) with concrete implementations in the infrastructure layer. Provider selection happens at dependency injection time based on configuration.

## Interface

```python
class LLMService(ABC):
    @abstractmethod
    async def generate(
        self, question: Question, context_chunks: list[Chunk]
    ) -> str: ...
```

The LLM service receives the question and context chunks, and returns the generated text. It does **not** build source references — that responsibility belongs to the `AskQuestion` use case, which has access to document metadata via the repository.

## Implementations

| Provider   | Class                  | Config value          |
|------------|------------------------|-----------------------|
| OpenAI     | `OpenAILLMService`     | `LLM_PROVIDER=openai` |
| Anthropic  | `AnthropicLLMService`  | `LLM_PROVIDER=anthropic` |

Both implementations share the same system prompt structure: context chunks are formatted with source identifiers, and the LLM is instructed to answer only from the provided context.

## Configuration

Controlled via environment variables:

- `LLM_PROVIDER` — `"openai"` (default) or `"anthropic"`
- `LLM_MODEL` — model identifier (e.g., `"gpt-4o-mini"`, `"claude-sonnet-4-5-20250929"`)
- `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` — provider credentials

## Why the LLM Doesn't Build Sources

Source references require document titles, which the LLM service doesn't have access to (chunks only carry `document_id`). The `AskQuestion` use case resolves titles via `DocumentRepository.find_by_id()` and builds the source list using the actual similarity scores from the vector search. This keeps the LLM service focused on text generation.

## Error Handling

Both implementations catch provider-specific exceptions and wrap them in `LLMGenerationError` (a domain exception), which the error handler maps to HTTP 502.
