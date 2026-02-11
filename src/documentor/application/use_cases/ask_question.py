from documentor.domain.models.question import Question
from documentor.domain.services.embedding_service import EmbeddingService
from documentor.domain.services.llm_service import LLMService
from documentor.domain.unit_of_work import UnitOfWork

from documentor.application.dtos import AnswerDTO, AskQuestionInput, SourceReferenceDTO


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

            chunks = [chunk for chunk, _score in results]
            text = await self._llm_service.generate(question, chunks)

            document_titles: dict[str, str] = {}
            for chunk, _score in results:
                if chunk.document_id not in document_titles:
                    doc = await self._uow.documents.find_by_id(chunk.document_id)
                    document_titles[chunk.document_id] = (
                        doc.title if doc else chunk.document_id
                    )

        sources = [
            SourceReferenceDTO(
                document_title=document_titles[chunk.document_id],
                chunk_text=chunk.content.text,
                relevance_score=score,
                chunk_id=chunk.id,
            )
            for chunk, score in results
        ]

        return AnswerDTO(text=text, sources=sources)
