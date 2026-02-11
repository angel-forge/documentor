from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from uuid_utils import uuid7

from documentor.domain.exceptions import InvalidDocumentError


class SourceType(StrEnum):
    URL = "url"
    FILE = "file"
    TEXT = "text"


@dataclass
class Document:
    id: str
    source: str
    title: str
    source_type: SourceType
    created_at: datetime
    chunk_count: int = 0

    def __post_init__(self) -> None:
        if not self.source or not self.source.strip():
            raise InvalidDocumentError("Document source cannot be empty")
        if not self.title or not self.title.strip():
            raise InvalidDocumentError("Document title cannot be empty")
        if self.created_at.tzinfo is None:
            raise InvalidDocumentError("created_at must be timezone-aware")

    @classmethod
    def create(
        cls,
        source: str,
        title: str,
        source_type: SourceType,
        chunk_count: int = 0,
    ) -> "Document":
        return cls(
            id=str(uuid7()),
            source=source,
            title=title,
            source_type=source_type,
            created_at=datetime.now(UTC),
            chunk_count=chunk_count,
        )
