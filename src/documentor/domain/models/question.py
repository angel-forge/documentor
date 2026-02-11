from dataclasses import dataclass

from documentor.domain.exceptions import InvalidQuestionError

MAX_QUESTION_LENGTH = 1000


@dataclass(frozen=True)
class Question:
    text: str

    def __post_init__(self) -> None:
        if not self.text or not self.text.strip():
            raise InvalidQuestionError("Question text cannot be empty")
        if len(self.text) > MAX_QUESTION_LENGTH:
            raise InvalidQuestionError(
                f"Question text exceeds maximum length of {MAX_QUESTION_LENGTH} characters"
            )
