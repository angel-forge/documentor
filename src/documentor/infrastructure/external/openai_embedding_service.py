import tiktoken
from openai import AsyncOpenAI

from documentor.domain.exceptions import EmbeddingGenerationError
from documentor.domain.models.chunk import Embedding
from documentor.domain.services.embedding_service import EmbeddingService


class OpenAIEmbeddingService(EmbeddingService):
    def __init__(self, api_key: str, model: str = "text-embedding-3-small") -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model
        self._encoding = tiktoken.encoding_for_model(model)

    async def embed(self, text: str) -> Embedding:
        try:
            response = await self._client.embeddings.create(
                model=self._model, input=text
            )
            return Embedding.from_list(response.data[0].embedding)
        except Exception as e:
            raise EmbeddingGenerationError(f"Failed to generate embedding: {e}") from e

    async def embed_batch(self, texts: list[str]) -> list[Embedding]:
        try:
            response = await self._client.embeddings.create(
                model=self._model, input=texts
            )
            sorted_data = sorted(response.data, key=lambda x: x.index)
            return [Embedding.from_list(item.embedding) for item in sorted_data]
        except Exception as e:
            raise EmbeddingGenerationError(
                f"Failed to generate embeddings batch: {e}"
            ) from e

    def count_tokens(self, text: str) -> int:
        return len(self._encoding.encode(text))
