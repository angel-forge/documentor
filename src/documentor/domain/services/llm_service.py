from abc import ABC, abstractmethod

from documentor.domain.models.chunk import Chunk
from documentor.domain.models.question import Question


class LLMService(ABC):
    @abstractmethod
    async def generate(
        self, question: Question, context_chunks: list[Chunk]
    ) -> str: ...
