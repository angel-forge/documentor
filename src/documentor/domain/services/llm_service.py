from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from documentor.domain.models.chunk import Chunk
from documentor.domain.models.conversation import ConversationMessage
from documentor.domain.models.question import Question


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
