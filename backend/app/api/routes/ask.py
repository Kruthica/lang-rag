import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.api.deps import get_rag_service
from app.core.logging_config import get_logger
from app.models.schemas import AskRequest, AskResponse
from app.services.rag_service import RAGService

router = APIRouter(tags=["chat"])
logger = get_logger(__name__)


@router.post("/ask", response_model=AskResponse)
async def ask_question(body: AskRequest) -> AskResponse:
    """Retrieve context and generate a grounded answer with source metadata."""
    rag: RAGService = get_rag_service()

    try:
        return await rag.ask(body.question, body.history)
    except TimeoutError as exc:
        logger.error("Ask timeout: %s", exc)
        return AskResponse(
            answer="The language model took too long to respond. Please try again.",
            sources=[],
        )
    except ValueError as exc:
        return AskResponse(answer=str(exc), sources=[])


@router.post("/ask/stream")
async def ask_question_stream(body: AskRequest):
    """Server-Sent Events stream of the assistant reply."""
    rag: RAGService = get_rag_service()

    async def event_generator():
        _, sources = rag.retrieve(body.question)
        # Send sources first so UI can render citations while text streams
        yield f"data: {json.dumps({'type': 'sources', 'sources': [s.model_dump() for s in sources]})}\n\n"

        async for token in rag.ask_stream(body.question, body.history):
            payload = json.dumps({"type": "token", "content": token})
            yield f"data: {payload}\n\n"

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
