from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from documentor.domain.models.chunk import Embedding
from documentor.domain.models.question import Question
from documentor.domain.services.embedding_service import EmbeddingService
from documentor.domain.services.llm_service import LLMService
from documentor.infrastructure.observability import (
    ObservedEmbeddingService,
    ObservedLLMService,
)


@contextmanager
def _noop_observation(**_kwargs: object) -> object:
    yield MagicMock()


@pytest.fixture
def _mock_langfuse():
    mock_client = MagicMock()
    mock_client.start_as_current_observation = MagicMock(side_effect=_noop_observation)
    with patch(
        "documentor.infrastructure.observability.get_client", return_value=mock_client
    ):
        yield


@pytest.fixture
def inner_llm() -> AsyncMock:
    return AsyncMock(spec=LLMService)


@pytest.fixture
def inner_embedding() -> AsyncMock:
    return AsyncMock(spec=EmbeddingService)


# --- ObservedLLMService ---


@pytest.mark.asyncio
@pytest.mark.usefixtures("_mock_langfuse")
async def test_generate_should_delegate_to_inner_and_return_result(
    inner_llm: AsyncMock,
) -> None:
    inner_llm.generate.return_value = "the answer"
    service = ObservedLLMService(inner_llm)
    question = Question(text="What is RAG?")

    result = await service.generate(question, [])

    assert result == "the answer"
    inner_llm.generate.assert_awaited_once_with(question, [], ())


@pytest.mark.asyncio
@pytest.mark.usefixtures("_mock_langfuse")
async def test_generate_stream_should_yield_all_chunks_from_inner(
    inner_llm: AsyncMock,
) -> None:
    async def fake_stream(*_args: object, **_kwargs: object):
        for token in ["Hello", " ", "world"]:
            yield token

    inner_llm.generate_stream = fake_stream
    service = ObservedLLMService(inner_llm)
    question = Question(text="What is RAG?")

    chunks = [chunk async for chunk in service.generate_stream(question, [])]

    assert chunks == ["Hello", " ", "world"]


@pytest.mark.asyncio
@pytest.mark.usefixtures("_mock_langfuse")
async def test_rewrite_query_should_delegate_to_inner_and_return_result(
    inner_llm: AsyncMock,
) -> None:
    inner_llm.rewrite_query.return_value = "rewritten query"
    service = ObservedLLMService(inner_llm)
    question = Question(text="What is RAG?")
    history = ()

    result = await service.rewrite_query(question, history)

    assert result == "rewritten query"
    inner_llm.rewrite_query.assert_awaited_once_with(question, history)


# --- ObservedEmbeddingService ---


@pytest.mark.asyncio
@pytest.mark.usefixtures("_mock_langfuse")
async def test_embed_should_delegate_to_inner_and_return_result(
    inner_embedding: AsyncMock,
) -> None:
    embedding = Embedding.from_list([0.1, 0.2, 0.3])
    inner_embedding.embed.return_value = embedding
    service = ObservedEmbeddingService(inner_embedding)

    result = await service.embed("hello")

    assert result == embedding
    inner_embedding.embed.assert_awaited_once_with("hello")


@pytest.mark.asyncio
@pytest.mark.usefixtures("_mock_langfuse")
async def test_embed_batch_should_delegate_to_inner_and_return_result(
    inner_embedding: AsyncMock,
) -> None:
    embeddings = [Embedding.from_list([0.1, 0.2]), Embedding.from_list([0.3, 0.4])]
    inner_embedding.embed_batch.return_value = embeddings
    service = ObservedEmbeddingService(inner_embedding)

    result = await service.embed_batch(["a", "b"])

    assert result == embeddings
    inner_embedding.embed_batch.assert_awaited_once_with(["a", "b"])


@pytest.mark.usefixtures("_mock_langfuse")
def test_count_tokens_should_delegate_to_inner(inner_embedding: AsyncMock) -> None:
    inner_embedding.count_tokens.return_value = 42
    service = ObservedEmbeddingService(inner_embedding)

    result = service.count_tokens("hello world")

    assert result == 42
    inner_embedding.count_tokens.assert_called_once_with("hello world")
