from documentor.domain.models.question import Question
from documentor.domain.repositories.chunk_repository import ChunkRepository
from documentor.domain.services.embedding_service import EmbeddingService
from documentor.domain.services.llm_service import LLMService

from documentor.application.dtos import AnswerDTO, AskQuestionInput, SourceReferenceDTO


class AskQuestion:
    def __init__(
        self,
        embedding_service: EmbeddingService,
        chunk_repository: ChunkRepository,
        llm_service: LLMService,
    ) -> None:
        self._embedding_service = embedding_service
        self._chunk_repository = chunk_repository
        self._llm_service = llm_service

    async def execute(self, input: AskQuestionInput) -> AnswerDTO:
        """Process a question using RAG: embed, search, generate."""
        question = Question(text=input.question_text)

        embedding = await self._embedding_service.embed(question.text)
        results = await self._chunk_repository.search_similar(embedding, top_k=5)

        chunks = [chunk for chunk, _score in results]
        answer = await self._llm_service.generate(question, chunks)

        sources = [
            SourceReferenceDTO(
                document_title=source.document_title,
                chunk_text=source.chunk_text,
                relevance_score=source.relevance_score,
                chunk_id=source.chunk_id,
            )
            for source in answer.sources
        ]

        return AnswerDTO(text=answer.text, sources=sources)
