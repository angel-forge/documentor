from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, MagicMock

import pytest

from documentor.application.dtos import AskQuestionInput
from documentor.application.use_cases.ask_question import AskQuestion
from documentor.domain.exceptions import InvalidQuestionError
from documentor.domain.models.chunk import Chunk, ChunkContent, Embedding
from documentor.domain.models.conversation import ConversationMessage
from documentor.domain.models.document import Document, SourceType


@pytest.fixture
def sample_chunk() -> Chunk:
    chunk = Chunk.create(
        document_id="doc-1",
        content=ChunkContent(text="Python is a programming language.", token_count=5),
        position=0,
    )
    chunk.set_embedding(Embedding.from_list([0.1, 0.2, 0.3]))
    return chunk


@pytest.fixture
def sample_document() -> Document:
    return Document.create(
        source="https://docs.python.org",
        title="Python Docs",
        source_type=SourceType.URL,
        chunk_count=1,
    )


@pytest.fixture
def embedding_service() -> AsyncMock:
    mock = AsyncMock()
    mock.embed.return_value = Embedding.from_list([0.1, 0.2, 0.3])
    return mock


@pytest.fixture
def llm_service() -> AsyncMock:
    mock = AsyncMock()
    mock.generate.return_value = "Python is a popular programming language."
    return mock


@pytest.fixture
def uow(sample_chunk: Chunk, sample_document: Document) -> AsyncMock:
    mock = AsyncMock()
    mock.__aenter__.return_value = mock
    mock.chunks.search_similar.return_value = [(sample_chunk, 0.95)]
    mock.documents.find_by_ids.return_value = {
        sample_chunk.document_id: sample_document
    }
    return mock


@pytest.fixture
def use_case(
    embedding_service: AsyncMock,
    llm_service: AsyncMock,
    uow: AsyncMock,
) -> AskQuestion:
    return AskQuestion(
        embedding_service=embedding_service,
        llm_service=llm_service,
        uow=uow,
    )


@pytest.mark.asyncio
async def test_execute_should_return_answer_with_sources_when_relevant_chunks_exist(
    use_case: AskQuestion,
) -> None:
    input_dto = AskQuestionInput(question_text="What is Python?")

    result = await use_case.execute(input_dto)

    assert result.text == "Python is a popular programming language."
    assert len(result.sources) == 1
    assert result.sources[0].document_title == "Python Docs"
    assert result.sources[0].relevance_score == 0.95


@pytest.mark.asyncio
async def test_execute_should_embed_question_and_search_chunks_when_asking(
    use_case: AskQuestion,
    embedding_service: AsyncMock,
    uow: AsyncMock,
) -> None:
    input_dto = AskQuestionInput(question_text="What is Python?")

    await use_case.execute(input_dto)

    embedding_service.embed.assert_awaited_once_with("What is Python?")
    uow.chunks.search_similar.assert_awaited_once()
    call_args = uow.chunks.search_similar.call_args
    assert call_args[0][0] == Embedding.from_list([0.1, 0.2, 0.3])
    assert call_args[1]["top_k"] == 5


@pytest.mark.asyncio
async def test_execute_should_raise_error_when_question_is_empty(
    use_case: AskQuestion,
) -> None:
    input_dto = AskQuestionInput(question_text="")

    with pytest.raises(InvalidQuestionError):
        await use_case.execute(input_dto)


@pytest.mark.asyncio
async def test_execute_should_batch_lookup_document_titles_when_building_sources(
    use_case: AskQuestion,
    uow: AsyncMock,
    sample_chunk: Chunk,
) -> None:
    input_dto = AskQuestionInput(question_text="What is Python?")

    await use_case.execute(input_dto)

    uow.documents.find_by_ids.assert_awaited_once_with({sample_chunk.document_id})


@pytest.mark.asyncio
async def test_execute_should_return_no_results_message_when_no_chunks_found(
    embedding_service: AsyncMock,
    llm_service: AsyncMock,
) -> None:
    uow = AsyncMock()
    uow.__aenter__.return_value = uow
    uow.chunks.search_similar.return_value = []

    use_case = AskQuestion(
        embedding_service=embedding_service,
        llm_service=llm_service,
        uow=uow,
    )
    input_dto = AskQuestionInput(question_text="What is Python?")

    result = await use_case.execute(input_dto)

    assert result.text == "No relevant documentation found for your question."
    assert result.sources == []
    llm_service.generate.assert_not_awaited()


@pytest.mark.asyncio
async def test_execute_should_discard_low_relevance_chunks_when_below_threshold(
    sample_chunk: Chunk,
    sample_document: Document,
    embedding_service: AsyncMock,
    llm_service: AsyncMock,
) -> None:
    high_chunk = Chunk.create(
        document_id="doc-1",
        content=ChunkContent(text="Relevant content.", token_count=3),
        position=0,
    )
    low_chunk = Chunk.create(
        document_id="doc-1",
        content=ChunkContent(text="Irrelevant noise.", token_count=3),
        position=1,
    )

    uow = AsyncMock()
    uow.__aenter__.return_value = uow
    uow.chunks.search_similar.return_value = [(high_chunk, 0.8), (low_chunk, 0.1)]
    uow.documents.find_by_ids.return_value = {"doc-1": sample_document}

    use_case = AskQuestion(
        embedding_service=embedding_service,
        llm_service=llm_service,
        uow=uow,
    )
    input_dto = AskQuestionInput(question_text="What is Python?")

    result = await use_case.execute(input_dto)

    assert len(result.sources) == 1
    assert result.sources[0].relevance_score == 0.8


@pytest.mark.asyncio
async def test_execute_should_return_no_results_when_all_chunks_below_threshold(
    embedding_service: AsyncMock,
    llm_service: AsyncMock,
) -> None:
    low_chunk = Chunk.create(
        document_id="doc-1",
        content=ChunkContent(text="Irrelevant noise.", token_count=3),
        position=0,
    )

    uow = AsyncMock()
    uow.__aenter__.return_value = uow
    uow.chunks.search_similar.return_value = [(low_chunk, 0.2)]

    use_case = AskQuestion(
        embedding_service=embedding_service,
        llm_service=llm_service,
        uow=uow,
    )
    input_dto = AskQuestionInput(question_text="What is Python?")

    result = await use_case.execute(input_dto)

    assert result.text == "No relevant documentation found for your question."
    assert result.sources == []
    llm_service.generate.assert_not_awaited()


async def _async_gen(items: list[str]) -> AsyncIterator[str]:
    for item in items:
        yield item


@pytest.mark.asyncio
async def test_execute_stream_should_yield_text_events_and_sources_when_chunks_exist(
    sample_chunk: Chunk,
    sample_document: Document,
    embedding_service: AsyncMock,
    uow: AsyncMock,
) -> None:
    llm_service = AsyncMock()
    llm_service.generate_stream = MagicMock(
        side_effect=lambda q, c, h=(): _async_gen(["Hello", " world"])
    )

    use_case = AskQuestion(
        embedding_service=embedding_service,
        llm_service=llm_service,
        uow=uow,
    )
    input_dto = AskQuestionInput(question_text="What is Python?")

    events = [event async for event in use_case.execute_stream(input_dto)]

    text_events = [e for e in events if e["type"] == "text"]
    assert len(text_events) == 2
    assert text_events[0]["content"] == "Hello"
    assert text_events[1]["content"] == " world"

    sources_events = [e for e in events if e["type"] == "sources"]
    assert len(sources_events) == 1
    assert len(sources_events[0]["sources"]) == 1
    assert sources_events[0]["sources"][0]["document_title"] == "Python Docs"

    done_events = [e for e in events if e["type"] == "done"]
    assert len(done_events) == 1


@pytest.mark.asyncio
async def test_execute_stream_should_yield_no_results_when_no_chunks_found(
    embedding_service: AsyncMock,
    llm_service: AsyncMock,
) -> None:
    uow = AsyncMock()
    uow.__aenter__.return_value = uow
    uow.chunks.search_similar.return_value = []

    use_case = AskQuestion(
        embedding_service=embedding_service,
        llm_service=llm_service,
        uow=uow,
    )
    input_dto = AskQuestionInput(question_text="What is Python?")

    events = [event async for event in use_case.execute_stream(input_dto)]

    assert events[0] == {
        "type": "text",
        "content": "No relevant documentation found for your question.",
    }
    assert events[1] == {"type": "sources", "sources": []}
    assert events[2] == {"type": "done"}
    llm_service.generate_stream.assert_not_called()


@pytest.mark.asyncio
async def test_execute_should_pass_conversation_history_to_llm_when_provided(
    use_case: AskQuestion,
    llm_service: AsyncMock,
) -> None:
    history = (
        ConversationMessage(role="user", content="What is Python?"),
        ConversationMessage(role="assistant", content="A programming language."),
    )
    input_dto = AskQuestionInput(
        question_text="Tell me more", conversation_history=history
    )

    await use_case.execute(input_dto)

    call_args = llm_service.generate.call_args
    assert call_args[0][2] == history


@pytest.mark.asyncio
async def test_execute_should_embed_rewritten_query_when_history_provided(
    use_case: AskQuestion,
    embedding_service: AsyncMock,
    llm_service: AsyncMock,
) -> None:
    llm_service.rewrite_query.return_value = (
        "Tell me more about Python programming language"
    )
    history = (
        ConversationMessage(role="user", content="What is Python?"),
        ConversationMessage(role="assistant", content="A programming language."),
    )
    input_dto = AskQuestionInput(
        question_text="Tell me more", conversation_history=history
    )

    await use_case.execute(input_dto)

    llm_service.rewrite_query.assert_awaited_once()
    embedding_service.embed.assert_awaited_once_with(
        "Tell me more about Python programming language"
    )


@pytest.mark.asyncio
async def test_execute_stream_should_pass_conversation_history_to_llm_when_provided(
    sample_chunk: Chunk,
    sample_document: Document,
    embedding_service: AsyncMock,
    uow: AsyncMock,
) -> None:
    llm_service = AsyncMock()
    llm_service.generate_stream = MagicMock(
        side_effect=lambda q, c, h: _async_gen(["Hello"])
    )

    use_case = AskQuestion(
        embedding_service=embedding_service,
        llm_service=llm_service,
        uow=uow,
    )

    history = (
        ConversationMessage(role="user", content="What is Python?"),
        ConversationMessage(role="assistant", content="A programming language."),
    )
    input_dto = AskQuestionInput(
        question_text="Tell me more", conversation_history=history
    )

    events = [event async for event in use_case.execute_stream(input_dto)]
    assert any(e["type"] == "text" for e in events)

    call_args = llm_service.generate_stream.call_args
    assert call_args[0][2] == history


@pytest.mark.asyncio
async def test_execute_should_not_call_rewrite_query_when_no_history(
    use_case: AskQuestion,
    llm_service: AsyncMock,
    embedding_service: AsyncMock,
) -> None:
    input_dto = AskQuestionInput(question_text="What is Python?")

    await use_case.execute(input_dto)

    llm_service.rewrite_query.assert_not_awaited()
    embedding_service.embed.assert_awaited_once_with("What is Python?")


@pytest.mark.asyncio
async def test_execute_should_pass_original_question_to_generate_when_history_provided(
    use_case: AskQuestion,
    llm_service: AsyncMock,
) -> None:
    llm_service.rewrite_query.return_value = "Rewritten query about Python"
    history = (
        ConversationMessage(role="user", content="What is Python?"),
        ConversationMessage(role="assistant", content="A programming language."),
    )
    input_dto = AskQuestionInput(
        question_text="Tell me more", conversation_history=history
    )

    await use_case.execute(input_dto)

    call_args = llm_service.generate.call_args
    assert call_args[0][0].text == "Tell me more"
    assert call_args[0][2] == history


@pytest.mark.asyncio
async def test_execute_stream_should_call_rewrite_query_when_history_provided(
    sample_chunk: Chunk,
    sample_document: Document,
    embedding_service: AsyncMock,
    uow: AsyncMock,
) -> None:
    llm_service = AsyncMock()
    llm_service.rewrite_query.return_value = "Rewritten query"
    llm_service.generate_stream = MagicMock(
        side_effect=lambda q, c, h: _async_gen(["Hello"])
    )

    use_case = AskQuestion(
        embedding_service=embedding_service,
        llm_service=llm_service,
        uow=uow,
    )

    history = (
        ConversationMessage(role="user", content="What is Python?"),
        ConversationMessage(role="assistant", content="A programming language."),
    )
    input_dto = AskQuestionInput(
        question_text="Tell me more", conversation_history=history
    )

    events = [event async for event in use_case.execute_stream(input_dto)]
    assert any(e["type"] == "text" for e in events)

    llm_service.rewrite_query.assert_awaited_once()
    embedding_service.embed.assert_awaited_once_with("Rewritten query")


@pytest.mark.asyncio
async def test_execute_stream_should_not_call_rewrite_query_when_no_history(
    sample_chunk: Chunk,
    sample_document: Document,
    embedding_service: AsyncMock,
    uow: AsyncMock,
) -> None:
    llm_service = AsyncMock()
    llm_service.generate_stream = MagicMock(
        side_effect=lambda q, c, h=(): _async_gen(["Hello"])
    )

    use_case = AskQuestion(
        embedding_service=embedding_service,
        llm_service=llm_service,
        uow=uow,
    )
    input_dto = AskQuestionInput(question_text="What is Python?")

    events = [event async for event in use_case.execute_stream(input_dto)]
    assert any(e["type"] == "text" for e in events)

    llm_service.rewrite_query.assert_not_awaited()
    embedding_service.embed.assert_awaited_once_with("What is Python?")
