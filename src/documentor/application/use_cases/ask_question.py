from documentor.domain.models.answer import Answer, SourceReference
from documentor.domain.models.question import Question
from documentor.domain.services.embedding_service import EmbeddingService
from documentor.domain.services.llm_service import LLMService
from documentor.domain.unit_of_work import UnitOfWork

from documentor.application.dtos import AnswerDTO, AskQuestionInput


MIN_RELEVANCE_SCORE = 0.3


class AskQuestion:
    def __init__(
        self,
        embedding_service: EmbeddingService,
        llm_service: LLMService,
        uow: UnitOfWork,
    ) -> None:
        self._embedding_service = embedding_service
        self._llm_service = llm_service
        self._uow = uow

    async def execute(self, input: AskQuestionInput) -> AnswerDTO:
        """Process a question using RAG: embed, search, generate."""
        question = Question(text=input.question_text)

        embedding = await self._embedding_service.embed(question.text)

        async with self._uow:
            results = await self._uow.chunks.search_similar(embedding, top_k=5)
            results = [
                (chunk, score)
                for chunk, score in results
                if score >= MIN_RELEVANCE_SCORE
            ]

            if not results:
                return AnswerDTO(
                    text="No relevant documentation found for your question.",
                    sources=[],
                )

            chunks = [chunk for chunk, _score in results]
            text = await self._llm_service.generate(question, chunks)

            document_ids = {chunk.document_id for chunk, _score in results}
            documents = await self._uow.documents.find_by_ids(document_ids)
            document_titles = {
                doc_id: documents[doc_id].title if doc_id in documents else doc_id
                for doc_id in document_ids
            }

        answer = Answer(
            text=text,
            sources=tuple(
                SourceReference(
                    document_title=document_titles[chunk.document_id],
                    chunk_text=chunk.content.text,
                    relevance_score=score,
                    chunk_id=chunk.id,
                )
                for chunk, score in results
            ),
        )

        return AnswerDTO.from_domain(answer)
