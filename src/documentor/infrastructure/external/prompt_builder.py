from documentor.domain.models.chunk import Chunk


def build_rag_system_prompt(chunks: list[Chunk]) -> str:
    context_parts: list[str] = []
    for i, chunk in enumerate(chunks, 1):
        context_parts.append(
            f"[Source {i} | chunk_id={chunk.id} | document_id={chunk.document_id}]\n"
            f"{chunk.content.text}"
        )
    context = "\n\n".join(context_parts)
    return (
        "You are a helpful assistant that answers questions based on the provided "
        "documentation context. Use ONLY the information from the sources below to "
        "answer. If the answer cannot be found in the sources, say so clearly.\n\n"
        f"--- CONTEXT ---\n{context}\n--- END CONTEXT ---"
    )
