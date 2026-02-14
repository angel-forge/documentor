from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

from documentor.application.dtos import AskQuestionInput
from documentor.domain.exceptions import LLMGenerationError
from documentor.domain.models.conversation import ConversationMessage


@pytest.mark.asyncio
async def test_ask_should_return_answer_with_sources(
    client: AsyncClient,
    mock_ask_question: AsyncMock,
) -> None:
    response = await client.post("/ask", json={"question": "What is the answer?"})

    assert response.status_code == 200
    data = response.json()
    assert data["text"] == "The answer is 42."
    assert len(data["sources"]) == 1
    assert data["sources"][0]["document_title"] == "Example Docs"
    assert data["sources"][0]["relevance_score"] == 0.95
    mock_ask_question.execute.assert_called_once_with(
        AskQuestionInput(question_text="What is the answer?")
    )


@pytest.mark.asyncio
async def test_ask_should_return_422_when_question_missing(client: AsyncClient) -> None:
    response = await client.post("/ask", json={})

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_ask_should_return_502_when_llm_fails(
    client: AsyncClient,
    mock_ask_question: AsyncMock,
) -> None:
    mock_ask_question.execute.side_effect = LLMGenerationError(
        "LLM service unavailable"
    )

    response = await client.post("/ask", json={"question": "What is the answer?"})

    assert response.status_code == 502
    assert response.json() == {
        "detail": "Language model service is currently unavailable"
    }


@pytest.mark.asyncio
async def test_ask_should_accept_request_with_conversation_history(
    client: AsyncClient,
    mock_ask_question: AsyncMock,
) -> None:
    response = await client.post(
        "/ask",
        json={
            "question": "Tell me more",
            "history": [
                {"role": "user", "content": "What is Python?"},
                {"role": "assistant", "content": "A programming language."},
            ],
        },
    )

    assert response.status_code == 200
    mock_ask_question.execute.assert_called_once_with(
        AskQuestionInput(
            question_text="Tell me more",
            conversation_history=(
                ConversationMessage(role="user", content="What is Python?"),
                ConversationMessage(role="assistant", content="A programming language."),
            ),
        )
    )


@pytest.mark.asyncio
async def test_ask_should_return_422_when_history_has_invalid_role(
    client: AsyncClient,
) -> None:
    response = await client.post(
        "/ask",
        json={
            "question": "Tell me more",
            "history": [{"role": "invalid", "content": "Hello"}],
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_ask_should_return_422_when_history_message_has_empty_content(
    client: AsyncClient,
) -> None:
    response = await client.post(
        "/ask",
        json={
            "question": "Tell me more",
            "history": [{"role": "user", "content": ""}],
        },
    )

    assert response.status_code == 422
