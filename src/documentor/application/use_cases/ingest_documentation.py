from documentor.domain.models.chunk import Chunk, ChunkContent
from documentor.domain.models.document import Document
from documentor.domain.repositories.chunk_repository import ChunkRepository
from documentor.domain.repositories.document_repository import DocumentRepository
from documentor.domain.services.document_loader_service import DocumentLoaderService
from documentor.domain.services.embedding_service import EmbeddingService

from documentor.application.dtos import (
    DocumentDTO,
    IngestDocumentationInput,
    IngestResultDTO,
)


class IngestDocumentation:
    def __init__(
        self,
        loader: DocumentLoaderService,
        embedding_service: EmbeddingService,
        chunk_repository: ChunkRepository,
        document_repository: DocumentRepository,
    ) -> None:
        self._loader = loader
        self._embedding_service = embedding_service
        self._chunk_repository = chunk_repository
        self._document_repository = document_repository

    async def execute(self, input: IngestDocumentationInput) -> IngestResultDTO:
        """Ingest documentation from a source: load, chunk, embed, and store."""
        loaded = await self._loader.load(input.source)

        text_chunks = self._split_into_chunks(loaded.content)

        document = Document.create(
            source=input.source,
            title=loaded.title,
            source_type=loaded.source_type,
            chunk_count=len(text_chunks),
        )

        chunks: list[Chunk] = []
        for position, text in enumerate(text_chunks):
            token_count = len(text.split())
            content = ChunkContent(text=text, token_count=token_count)
            chunk = Chunk.create(
                document_id=document.id,
                content=content,
                position=position,
            )
            chunks.append(chunk)

        texts = [chunk.content.text for chunk in chunks]
        embeddings = await self._embedding_service.embed_batch(texts)

        for chunk, embedding in zip(chunks, embeddings, strict=True):
            chunk.set_embedding(embedding)

        await self._document_repository.save(document)
        await self._chunk_repository.save_all(chunks)

        return IngestResultDTO(
            document=DocumentDTO.from_entity(document),
            chunks_created=len(chunks),
        )

    def _split_into_chunks(
        self, text: str, chunk_size: int = 500, overlap: int = 50
    ) -> list[str]:
        words = text.split()
        if not words:
            return []

        chunks: list[str] = []
        start = 0
        while start < len(words):
            end = start + chunk_size
            chunk_text = " ".join(words[start:end])
            chunks.append(chunk_text)
            start += chunk_size - overlap

        return chunks
