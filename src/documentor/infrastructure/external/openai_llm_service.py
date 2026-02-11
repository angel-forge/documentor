from openai import AsyncOpenAI

from documentor.domain.exceptions import LLMGenerationError
from documentor.domain.models.answer import Answer, SourceReference
from documentor.domain.models.chunk import Chunk
from documentor.domain.models.question import Question
from documentor.domain.services.llm_service import LLMService


class OpenAILLMService(LLMService):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model

    async def generate(self, question: Question, context_chunks: list[Chunk]) -> Answer:
        try:
            system_prompt = _build_system_prompt(context_chunks)
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question.text},
                ],
            )
            text = response.choices[0].message.content or ""
            if not text.strip():
                raise LLMGenerationError("LLM returned empty response")
            sources = _build_sources(context_chunks)
            return Answer(text=text, sources=tuple(sources))
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


def _build_sources(chunks: list[Chunk]) -> list[SourceReference]:
    sources: list[SourceReference] = []
    for i, chunk in enumerate(chunks):
        score = max(0.0, 1.0 - (i * 0.1))
        sources.append(
            SourceReference(
                document_title=chunk.document_id,
                chunk_text=chunk.content.text,
                relevance_score=score,
                chunk_id=chunk.id,
            )
        )
    return sources
