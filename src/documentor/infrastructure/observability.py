from collections.abc import AsyncIterator
from typing import Any

from langfuse import get_client

from documentor.domain.models.chunk import Chunk, Embedding
from documentor.domain.models.conversation import ConversationMessage
from documentor.domain.models.question import Question
from documentor.domain.services.embedding_service import EmbeddingService
from documentor.domain.services.llm_service import LLMService


def _serialize_history(
    history: tuple[ConversationMessage, ...],
) -> list[dict[str, str]]:
    return [{"role": msg.role, "content": msg.content} for msg in history]


def _serialize_chunks(chunks: list[Chunk]) -> list[dict[str, Any]]:
    return [
        {
            "position": c.position,
            "text": c.content.text,
            "document_id": c.document_id,
        }
        for c in chunks
    ]


class ObservedLLMService(LLMService):
    def __init__(self, inner: LLMService) -> None:
        self._inner = inner

    async def generate(
        self,
        question: Question,
        context_chunks: list[Chunk],
        conversation_history: tuple[ConversationMessage, ...] = (),
    ) -> str:
        with get_client().start_as_current_observation(
            name="llm-generate",
            as_type="generation",
            input={
                "question": question.text,
                "conversation_history": _serialize_history(conversation_history),
                "context_chunks": _serialize_chunks(context_chunks),
            },
        ) as span:
            result = await self._inner.generate(
                question, context_chunks, conversation_history
            )
            span.update(output=result)
            return result

    async def generate_stream(
        self,
        question: Question,
        context_chunks: list[Chunk],
        conversation_history: tuple[ConversationMessage, ...] = (),
    ) -> AsyncIterator[str]:
        with get_client().start_as_current_observation(
            name="llm-generate-stream",
            as_type="generation",
            input={
                "question": question.text,
                "conversation_history": _serialize_history(conversation_history),
                "context_chunks": _serialize_chunks(context_chunks),
            },
        ) as span:
            collected: list[str] = []
            async for chunk in self._inner.generate_stream(
                question, context_chunks, conversation_history
            ):
                collected.append(chunk)
                yield chunk
            span.update(output="".join(collected))

    async def rewrite_query(
        self,
        question: Question,
        conversation_history: tuple[ConversationMessage, ...],
    ) -> str:
        with get_client().start_as_current_observation(
            name="llm-rewrite-query",
            as_type="generation",
            input={
                "question": question.text,
                "conversation_history": _serialize_history(conversation_history),
            },
        ) as span:
            result = await self._inner.rewrite_query(question, conversation_history)
            span.update(output=result)
            return result


class ObservedEmbeddingService(EmbeddingService):
    def __init__(self, inner: EmbeddingService) -> None:
        self._inner = inner

    async def embed(self, text: str) -> Embedding:
        with get_client().start_as_current_observation(
            name="embedding-embed",
            as_type="embedding",
            input={"text": text[:100]},
        ) as span:
            result = await self._inner.embed(text)
            span.update(output={"dimension": result.dimension})
            return result

    async def embed_batch(self, texts: list[str]) -> list[Embedding]:
        with get_client().start_as_current_observation(
            name="embedding-embed-batch",
            as_type="embedding",
            input={"count": len(texts)},
        ) as span:
            result = await self._inner.embed_batch(texts)
            span.update(output={"count": len(result)})
            return result

    def count_tokens(self, text: str) -> int:
        return self._inner.count_tokens(text)
