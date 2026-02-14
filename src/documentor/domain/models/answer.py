from dataclasses import dataclass

from documentor.domain.exceptions import InvalidAnswerError


@dataclass(frozen=True)
class SourceReference:
    document_title: str
    chunk_text: str
    relevance_score: float
    chunk_id: str

    def __post_init__(self) -> None:
        if not (0.0 <= self.relevance_score <= 1.0):
            raise InvalidAnswerError(
                f"Relevance score must be between 0.0 and 1.0, got {self.relevance_score}"
            )


@dataclass(frozen=True)
class Answer:
    text: str
    sources: tuple[SourceReference, ...]

    def __post_init__(self) -> None:
        if not self.text or not self.text.strip():
            raise InvalidAnswerError("Answer text cannot be empty")

    def has_sources(self) -> bool:
        return len(self.sources) > 0
