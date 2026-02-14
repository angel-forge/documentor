from openai import AsyncOpenAI

from documentor.domain.exceptions import LLMGenerationError
from documentor.domain.models.chunk import Chunk
from documentor.domain.models.question import Question
from documentor.domain.services.llm_service import LLMService
from documentor.infrastructure.external.prompt_builder import build_rag_system_prompt


class OpenAILLMService(LLMService):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model

    async def generate(self, question: Question, context_chunks: list[Chunk]) -> str:
        try:
            system_prompt = build_rag_system_prompt(context_chunks)
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
            return text
        except LLMGenerationError:
            raise
        except Exception as e:
            raise LLMGenerationError(f"Failed to generate answer: {e}") from e
