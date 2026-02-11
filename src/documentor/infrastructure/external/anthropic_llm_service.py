from anthropic import AsyncAnthropic

from documentor.domain.exceptions import LLMGenerationError
from documentor.domain.models.chunk import Chunk
from documentor.domain.models.question import Question
from documentor.domain.services.llm_service import LLMService


class AnthropicLLMService(LLMService):
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-5-20250929") -> None:
        self._client = AsyncAnthropic(api_key=api_key)
        self._model = model

    async def generate(self, question: Question, context_chunks: list[Chunk]) -> str:
        try:
            system_prompt = _build_system_prompt(context_chunks)
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=1024,
                system=system_prompt,
                messages=[{"role": "user", "content": question.text}],
            )
            return response.content[0].text
        except LLMGenerationError:
            raise
        except Exception as e:
            raise LLMGenerationError(f"Failed to generate answer: {e}") from e


def _build_system_prompt(chunks: list[Chunk]) -> str:
    context_parts: list[str] = []
    for i, chunk in enumerate(chunks, 1):
        context_parts.append(
            f"[Source {i} | chunk_id={chunk.id} | document_id={chunk.document_id}]\n"
            f"{chunk.content.text}"
        )
    context = "\n\n".join(context_parts)
    return (
        "You are a helpful assistant that answers questions based on the provided "
        "documentation context. Use ONLY the information from the sources below to "
        "answer. If the answer cannot be found in the sources, say so clearly.\n\n"
        f"--- CONTEXT ---\n{context}\n--- END CONTEXT ---"
    )
