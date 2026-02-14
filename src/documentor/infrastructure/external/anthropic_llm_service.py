from collections.abc import AsyncIterator

from anthropic import AsyncAnthropic
from anthropic.types import MessageParam

from documentor.domain.exceptions import LLMGenerationError
from documentor.domain.models.chunk import Chunk
from documentor.domain.models.conversation import ConversationMessage
from documentor.domain.models.question import Question
from documentor.domain.services.llm_service import LLMService
from documentor.infrastructure.external.prompt_builder import build_rag_system_prompt


def _build_history_messages(
    history: tuple[ConversationMessage, ...],
) -> list[MessageParam]:
    return [{"role": msg.role, "content": msg.content} for msg in history]


class AnthropicLLMService(LLMService):
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-5-20250929") -> None:
        self._client = AsyncAnthropic(api_key=api_key)
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
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=1024,
                system=system_prompt,
                messages=[*history_messages, {"role": "user", "content": question.text}],
            )
            if not response.content:
                raise LLMGenerationError("LLM returned empty response")
            return response.content[0].text
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
            async with self._client.messages.stream(
                model=self._model,
                max_tokens=1024,
                system=system_prompt,
                messages=[*history_messages, {"role": "user", "content": question.text}],
            ) as stream:
                async for text in stream.text_stream:
                    yield text
        except LLMGenerationError:
            raise
        except Exception as e:
            raise LLMGenerationError(f"Failed to generate answer: {e}") from e
