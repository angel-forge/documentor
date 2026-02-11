import pytest

from documentor.domain.exceptions import InvalidQuestionError
from documentor.domain.models.question import Question


class TestQuestion:
    def test_question_should_raise_error_when_text_is_empty(self) -> None:
        with pytest.raises(InvalidQuestionError, match="empty"):
            Question(text="")

    def test_question_should_raise_error_when_text_too_long(self) -> None:
        with pytest.raises(InvalidQuestionError, match="maximum length"):
            Question(text="a" * 1001)

    def test_question_should_accept_valid_text_when_within_limits(self) -> None:
        question = Question(text="What is Python?")
        assert question.text == "What is Python?"
