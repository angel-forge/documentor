import pytest

from documentor.domain.exceptions import InvalidChunkError
from documentor.domain.models.answer import Answer, SourceReference


class TestSourceReference:
    def test_source_reference_should_raise_error_when_relevance_out_of_range(
        self,
    ) -> None:
        with pytest.raises(InvalidChunkError, match="Relevance score"):
            SourceReference(
                document_title="Doc",
                chunk_text="text",
                relevance_score=1.5,
                chunk_id="c-1",
            )

        with pytest.raises(InvalidChunkError, match="Relevance score"):
            SourceReference(
                document_title="Doc",
                chunk_text="text",
                relevance_score=-0.1,
                chunk_id="c-1",
            )


class TestAnswer:
    def test_answer_should_raise_error_when_text_is_empty(self) -> None:
        with pytest.raises(InvalidChunkError, match="Answer text"):
            Answer(text="", sources=())

    def test_answer_has_sources_should_return_true_when_present(self) -> None:
        source = SourceReference(
            document_title="Doc",
            chunk_text="text",
            relevance_score=0.9,
            chunk_id="c-1",
        )
        answer = Answer(text="The answer is 42", sources=(source,))
        assert answer.has_sources() is True

    def test_answer_has_sources_should_return_false_when_empty(self) -> None:
        answer = Answer(text="No sources available", sources=())
        assert answer.has_sources() is False
