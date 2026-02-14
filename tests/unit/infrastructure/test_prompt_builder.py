from documentor.domain.models.conversation import ConversationMessage
from documentor.domain.models.question import Question
from documentor.infrastructure.external.prompt_builder import (
    MAX_REWRITE_HISTORY_CHARS,
    MAX_REWRITE_HISTORY_MESSAGES,
    build_query_rewrite_prompt,
    build_rewrite_user_message,
)


def test_build_query_rewrite_prompt_should_return_non_empty_system_prompt() -> None:
    prompt = build_query_rewrite_prompt()

    assert isinstance(prompt, str)
    assert len(prompt) > 0
    assert "rewrite" in prompt.lower()


def test_build_rewrite_user_message_should_include_history_and_question() -> None:
    question = Question(text="Tell me more")
    history = (
        ConversationMessage(role="user", content="What is Python?"),
        ConversationMessage(role="assistant", content="A programming language."),
    )

    message = build_rewrite_user_message(question, history)

    assert "What is Python?" in message
    assert "A programming language." in message
    assert "Tell me more" in message
    assert "User:" in message
    assert "Assistant:" in message


def test_build_rewrite_user_message_should_preserve_history_order() -> None:
    question = Question(text="And what about JavaScript?")
    history = (
        ConversationMessage(role="user", content="First question"),
        ConversationMessage(role="assistant", content="First answer"),
        ConversationMessage(role="user", content="Second question"),
        ConversationMessage(role="assistant", content="Second answer"),
    )

    message = build_rewrite_user_message(question, history)

    first_pos = message.index("First question")
    second_pos = message.index("Second question")
    question_pos = message.index("And what about JavaScript?")
    assert first_pos < second_pos < question_pos


def test_build_rewrite_user_message_should_keep_only_recent_messages_when_history_exceeds_limit() -> (
    None
):
    question = Question(text="Follow up")
    history = tuple(
        ConversationMessage(
            role="user" if i % 2 == 0 else "assistant",
            content=f"Message {i}",
        )
        for i in range(MAX_REWRITE_HISTORY_MESSAGES + 6)
    )

    message = build_rewrite_user_message(question, history)

    assert "Message 0" not in message
    assert "Message 5" not in message
    assert f"Message {len(history) - 1}" in message


def test_build_rewrite_user_message_should_truncate_when_history_exceeds_char_limit() -> (
    None
):
    question = Question(text="Follow up")
    long_content = "x" * (MAX_REWRITE_HISTORY_CHARS + 500)
    history = (
        ConversationMessage(role="user", content=long_content),
        ConversationMessage(role="assistant", content="Should not appear"),
    )

    message = build_rewrite_user_message(question, history)

    assert "Should not appear" not in message
    assert "..." in message
    assert "Follow up" in message
