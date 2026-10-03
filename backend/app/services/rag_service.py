import asyncio
from typing import AsyncIterator, List, Tuple
import os
from huggingface_hub import InferenceClient
from langchain_core.documents import Document

from app.core.config import Settings, get_settings
from app.core.logging_config import get_logger
from app.models.schemas import AskResponse, ChatMessage, SourceChunk
from app.services.chat_memory import format_history
from app.services.vector_store import VectorStoreService

logger = get_logger(__name__)

TOP_K = 8

SYSTEM_PROMPT = """
You are an intelligent, conversational, and highly capable research assistant.
Your goal is to provide clear, concise, and helpful answers based ONLY on the provided context.

Instructions:
1. Synthesize the provided context to answer the user's question directly and naturally.
2. DO NOT use robotic phrases like "Based on the provided context, it appears that..." or "The document mentions...". Just answer the question directly as if you already know the information.
3. If the context does not contain the answer, simply state politely that the provided documents don't contain enough information to answer that specific question. Do not guess.
4. Use markdown formatting (bullet points, bold text) to make your answers easy to read.
"""

USER_PROMPT_TEMPLATE = """{history}

Context from documents:
{context}

Question:
{question}

Answer using only the context above.
"""


def _distance_to_confidence(distance: float) -> float:

    if distance <= 0:
        return 1.0

    return max(0.0, min(1.0, 1.0 / (1.0 + distance)))


def _build_context(
    docs_with_scores: List[Tuple[Document, float]]
) -> Tuple[str, List[SourceChunk]]:

    parts: List[str] = []
    sources: List[SourceChunk] = []

    for idx, (doc, score) in enumerate(docs_with_scores, start=1):

        meta = doc.metadata or {}

        filename = str(meta.get("source", "unknown"))
        page = meta.get("page")

        confidence = _distance_to_confidence(float(score))

        header = f"[{idx}] {filename}"

        if page is not None:
            header += f" (page {page})"

        parts.append(f"{header}\n{doc.page_content}")

        sources.append(
            SourceChunk(
                content=doc.page_content[:500],
                filename=filename,
                page=int(page) if page is not None else None,
                score=round(confidence, 4),
                metadata=dict(meta),
            )
        )

    return "\n\n---\n\n".join(parts), sources


class RAGService:

    def __init__(
        self,
        settings: Settings | None = None,
        vector_store: VectorStoreService | None = None,
    ):

        self.settings = settings or get_settings()

        self.vector_store = (
            vector_store or VectorStoreService(self.settings)
        )

        self._llm = None

    def _get_llm(self):

        if self._llm is None:

            self._llm = InferenceClient(
                api_key=os.getenv("HF_TOKEN")
            )

        return self._llm

    def retrieve(
        self,
        question: str,
        k: int = TOP_K,
    ) -> Tuple[str, List[SourceChunk]]:

        results = self.vector_store.similarity_search_with_score(
            question,
            k=k,
        )

        if not results:
            return "", []

        return _build_context(results)

    async def ask(
        self,
        question: str,
        history: List[ChatMessage] | None = None,
    ) -> AskResponse:

        history = history or []

        context, sources = self.retrieve(question)

        if not context.strip():
            return AskResponse(
                answer="No documents indexed yet.",
                sources=[],
            )

        history_text = format_history(history)

        user_content = USER_PROMPT_TEMPLATE.format(
            history=history_text,
            context=context,
            question=question,
        )

        llm = self._get_llm()

        try:

            response = await asyncio.to_thread(
                llm.chat_completion,
                model="meta-llama/Llama-3.1-8B-Instruct",
                messages=[
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": user_content,
                    },
                ],
                max_tokens=512,
                temperature=0.2,
            )

            answer = response.choices[0].message.content

        except Exception as exc:

            logger.exception("LLM invocation failed")

            raise Exception(
                f"LLM request failed: {exc}"
            ) from exc

        return AskResponse(
            answer=answer,
            sources=sources,
        )

    async def ask_stream(
        self,
        question: str,
        history: List[ChatMessage] | None = None,
    ) -> AsyncIterator[str]:

        response = await self.ask(question, history)

        yield response.answer