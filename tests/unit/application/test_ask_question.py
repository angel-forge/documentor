from unittest.mock import AsyncMock

import pytest

from documentor.application.dtos import AskQuestionInput
from documentor.application.use_cases.ask_question import AskQuestion
from documentor.domain.exceptions import InvalidQuestionError
from documentor.domain.models.chunk import Chunk, ChunkContent, Embedding
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
    mock.documents.find_by_ids.return_value = {sample_chunk.document_id: sample_document}
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
