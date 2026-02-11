from dataclasses import dataclass
from uuid_utils import uuid7

from documentor.domain.exceptions import InvalidChunkError, InvalidEmbeddingError


@dataclass(frozen=True)
class Embedding:
    vector: tuple[float, ...]
    dimension: int

    def __post_init__(self) -> None:
        if len(self.vector) != self.dimension:
            raise InvalidEmbeddingError(
                f"Vector length {len(self.vector)} does not match dimension {self.dimension}"
            )

    @classmethod
    def from_list(cls, values: list[float]) -> "Embedding":
        return cls(vector=tuple(values), dimension=len(values))


@dataclass(frozen=True)
class ChunkContent:
    text: str
    token_count: int

    def __post_init__(self) -> None:
        if not self.text or not self.text.strip():
            raise InvalidChunkError("Chunk text cannot be empty")
        if self.token_count <= 0:
            raise InvalidChunkError("Token count must be greater than 0")


@dataclass
class Chunk:
    id: str
    document_id: str
    content: ChunkContent
    position: int
    embedding: Embedding | None = None

    @classmethod
    def create(
        cls,
        document_id: str,
        content: ChunkContent,
        position: int,
    ) -> "Chunk":
        return cls(
            id=str(uuid7()),
            document_id=document_id,
            content=content,
            position=position,
        )

    def set_embedding(self, embedding: Embedding) -> None:
        self.embedding = embedding

    def has_embedding(self) -> bool:
        return self.embedding is not None
