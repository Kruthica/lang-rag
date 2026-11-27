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
        try:
            response = await rag.ask(body.question, body.history)
            sources = [source.model_dump() for source in response.sources]
            yield f"data: {json.dumps({'type': 'sources', 'sources': sources})}\n\n"
            yield f"data: {json.dumps({'type': 'token', 'content': response.answer})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except Exception:
            logger.exception("Streaming answer failed")
            yield f"data: {json.dumps({'type': 'error', 'detail': 'Could not generate an answer. Please try again.'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
