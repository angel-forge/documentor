import pytest

from documentor.domain.exceptions import InvalidQuestionError
from documentor.domain.models.conversation import ConversationMessage


def test_create_user_message_should_succeed_when_content_valid() -> None:
    msg = ConversationMessage(role="user", content="Hello")

    assert msg.role == "user"
    assert msg.content == "Hello"


def test_create_assistant_message_should_succeed_when_content_valid() -> None:
    msg = ConversationMessage(role="assistant", content="Hi there")

    assert msg.role == "assistant"
    assert msg.content == "Hi there"


def test_create_should_raise_when_content_empty() -> None:
    with pytest.raises(InvalidQuestionError, match="cannot be empty"):
        ConversationMessage(role="user", content="")


def test_create_should_raise_when_content_whitespace() -> None:
    with pytest.raises(InvalidQuestionError, match="cannot be empty"):
        ConversationMessage(role="user", content="   ")


def test_message_should_be_immutable() -> None:
    msg = ConversationMessage(role="user", content="Hello")

    with pytest.raises(AttributeError):
        msg.content = "Changed"  # type: ignore[misc]


def test_messages_should_be_equal_when_same_values() -> None:
    msg1 = ConversationMessage(role="user", content="Hello")
    msg2 = ConversationMessage(role="user", content="Hello")

    assert msg1 == msg2


def test_messages_should_differ_when_different_roles() -> None:
    msg1 = ConversationMessage(role="user", content="Hello")
    msg2 = ConversationMessage(role="assistant", content="Hello")

    assert msg1 != msg2
