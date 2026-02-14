import json
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from documentor.adapters.api.dependencies import get_ask_question
from documentor.adapters.api.schemas import (
    AnswerResponse,
    AskQuestionRequest,
    SourceReferenceResponse,
)
from documentor.application.dtos import AskQuestionInput
from documentor.application.use_cases.ask_question import AskQuestion

router = APIRouter()


@router.post("/ask", response_model=AnswerResponse)
async def ask_question(
    request: AskQuestionRequest,
    use_case: Annotated[AskQuestion, Depends(get_ask_question)],
) -> AnswerResponse:
    """Ask a question about the ingested documentation."""
    result = await use_case.execute(AskQuestionInput(question_text=request.question))
    return AnswerResponse(
        text=result.text,
        sources=[
            SourceReferenceResponse(
                document_title=src.document_title,
                chunk_text=src.chunk_text,
                relevance_score=src.relevance_score,
                chunk_id=src.chunk_id,
            )
            for src in result.sources
        ],
    )


@router.post("/ask/stream")
async def ask_question_stream(
    request: AskQuestionRequest,
    use_case: Annotated[AskQuestion, Depends(get_ask_question)],
) -> StreamingResponse:
    """Ask a question and receive a streamed NDJSON response."""
    input_dto = AskQuestionInput(question_text=request.question)

    async def event_generator():
        async for event in use_case.execute_stream(input_dto):
            yield json.dumps(event) + "\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")
