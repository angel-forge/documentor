from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from documentor.domain.models.chunk import Chunk
from documentor.domain.models.question import Question


class LLMService(ABC):
    @abstractmethod
    async def generate(
        self, question: Question, context_chunks: list[Chunk]
    ) -> str: ...

    @abstractmethod
    def generate_stream(
        self, question: Question, context_chunks: list[Chunk]
    ) -> AsyncIterator[str]: ...
