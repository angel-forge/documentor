from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from documentor.infrastructure.external.openai_embedding_service import (
    OpenAIEmbeddingService,
    _MAX_BATCH_SIZE,
)


def _make_embedding_response(count: int, vector: list[float] | None = None) -> object:
    """Build a fake OpenAI embeddings response with `count` items."""
    vec = vector or [0.1, 0.2, 0.3]
    return SimpleNamespace(
        data=[SimpleNamespace(index=i, embedding=vec) for i in range(count)]
    )


@pytest.fixture
def service() -> OpenAIEmbeddingService:
    with patch("tiktoken.encoding_for_model"):
        return OpenAIEmbeddingService(api_key="test-key")


@pytest.mark.asyncio
async def test_embed_batch_should_make_single_call_when_within_limit(
    service: OpenAIEmbeddingService,
) -> None:
    texts = [f"text-{i}" for i in range(10)]
    service._client.embeddings.create = AsyncMock(
        return_value=_make_embedding_response(10)
    )

    result = await service.embed_batch(texts)

    assert len(result) == 10
    service._client.embeddings.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_embed_batch_should_split_into_batches_when_exceeding_limit(
    service: OpenAIEmbeddingService,
) -> None:
    total = _MAX_BATCH_SIZE + 100
    texts = [f"text-{i}" for i in range(total)]

    service._client.embeddings.create = AsyncMock(
        side_effect=[
            _make_embedding_response(_MAX_BATCH_SIZE),
            _make_embedding_response(100),
        ]
    )

    result = await service.embed_batch(texts)

    assert len(result) == total
    assert service._client.embeddings.create.await_count == 2

    first_call_input = service._client.embeddings.create.call_args_list[0].kwargs[
        "input"
    ]
    second_call_input = service._client.embeddings.create.call_args_list[1].kwargs[
        "input"
    ]
    assert len(first_call_input) == _MAX_BATCH_SIZE
    assert len(second_call_input) == 100


@pytest.mark.asyncio
async def test_embed_batch_should_return_empty_list_when_no_texts(
    service: OpenAIEmbeddingService,
) -> None:
    result = await service.embed_batch([])

    assert result == []
