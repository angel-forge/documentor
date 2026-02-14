from collections.abc import AsyncIterator

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam

from documentor.domain.exceptions import LLMGenerationError
from documentor.domain.models.chunk import Chunk
from documentor.domain.models.conversation import ConversationMessage
from documentor.domain.models.question import Question
from documentor.domain.services.llm_service import LLMService
from documentor.infrastructure.external.prompt_builder import build_rag_system_prompt


def _build_history_messages(
    history: tuple[ConversationMessage, ...],
) -> list[ChatCompletionMessageParam]:
    return [{"role": msg.role, "content": msg.content} for msg in history]


class OpenAILLMService(LLMService):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model

    async def generate(
        self,
        question: Question,
        context_chunks: list[Chunk],
        conversation_history: tuple[ConversationMessage, ...] = (),
    ) -> str:
        try:
            system_prompt = build_rag_system_prompt(context_chunks)
            history_messages = _build_history_messages(conversation_history)
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    *history_messages,
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

    async def generate_stream(
        self,
        question: Question,
        context_chunks: list[Chunk],
        conversation_history: tuple[ConversationMessage, ...] = (),
    ) -> AsyncIterator[str]:
        try:
            system_prompt = build_rag_system_prompt(context_chunks)
            history_messages = _build_history_messages(conversation_history)
            stream = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    *history_messages,
                    {"role": "user", "content": question.text},
                ],
                stream=True,
            )
            async for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
        except LLMGenerationError:
            raise
        except Exception as e:
            raise LLMGenerationError(f"Failed to generate answer: {e}") from e
