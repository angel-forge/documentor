from documentor.domain.models.chunk import Chunk
from documentor.domain.models.conversation import ConversationMessage
from documentor.domain.models.question import Question


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


def build_query_rewrite_prompt() -> str:
    return (
        "You are a query rewriter for a documentation search system. "
        "Given a conversation history and a follow-up question, rewrite the "
        "follow-up into a standalone, self-contained search query that captures "
        "the full intent. The rewritten query should be concise and suitable for "
        "semantic search against technical documentation. "
        "Output ONLY the rewritten query, nothing else."
    )


MAX_REWRITE_HISTORY_MESSAGES = 10
MAX_REWRITE_HISTORY_CHARS = 2000


def build_rewrite_user_message(
    question: Question,
    conversation_history: tuple[ConversationMessage, ...],
) -> str:
    recent = conversation_history[-MAX_REWRITE_HISTORY_MESSAGES:]

    history_lines: list[str] = []
    total_chars = 0
    for msg in recent:
        label = "User" if msg.role == "user" else "Assistant"
        line = f"{label}: {msg.content}"
        if total_chars + len(line) > MAX_REWRITE_HISTORY_CHARS:
            remaining = MAX_REWRITE_HISTORY_CHARS - total_chars
            if remaining > 0:
                history_lines.append(line[:remaining] + "...")
            break
        history_lines.append(line)
        total_chars += len(line)

    history_block = "\n".join(history_lines)
    return (
        f"--- CONVERSATION HISTORY ---\n{history_block}\n"
        f"--- END CONVERSATION HISTORY ---\n\n"
        f"Follow-up question: {question.text}"
    )
