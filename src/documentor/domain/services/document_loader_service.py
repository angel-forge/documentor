from abc import ABC, abstractmethod
from dataclasses import dataclass

from documentor.domain.models.document import SourceType


@dataclass(frozen=True)
class LoadedDocument:
    content: str
    title: str
    source_type: SourceType


class DocumentLoaderService(ABC):
    @abstractmethod
    async def load(self, source: str) -> LoadedDocument: ...
