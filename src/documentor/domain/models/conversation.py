from dataclasses import dataclass
from typing import Literal

from documentor.domain.exceptions import InvalidQuestionError


@dataclass(frozen=True)
class ConversationMessage:
    role: Literal["user", "assistant"]
    content: str

    def __post_init__(self) -> None:
        if not self.content or not self.content.strip():
            raise InvalidQuestionError("Conversation message content cannot be empty")
