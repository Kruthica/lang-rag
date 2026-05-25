"""
ChromaDB vector store — persistent local storage with deduplication.

Existing collections are reused on restart. Before ingesting, we check whether
a document_id already has vectors to avoid duplicate embeddings.
"""

from pathlib import Path
from typing import List, Optional, Tuple

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from app.core.config import Settings, get_settings
from app.core.logging_config import get_logger
from app.services.embedding_service import get_embeddings

logger = get_logger(__name__)


class VectorStoreError(Exception):
    pass


class VectorStoreService:
    """Thin wrapper around LangChain Chroma with project-specific helpers."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self.persist_dir = Path(self.settings.chroma_db_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self._store: Optional[Chroma] = None

    @property
    def embeddings(self) -> Embeddings:
        # Embeddings are cached globally via get_settings(); do not pass Settings
        # to lru_cache (Pydantic models are unhashable).
        return get_embeddings()

    def get_store(self) -> Chroma:
        if self._store is None:
            self._store = Chroma(
                collection_name=self.settings.collection_name,
                embedding_function=self.embeddings,
                persist_directory=str(self.persist_dir),
            )
            logger.info("Chroma collection ready at %s", self.persist_dir)
        return self._store

    def document_already_indexed(self, document_id: str) -> bool:
        """Return True if any vectors exist for this document_id."""
        store = self.get_store()
        try:
            result = store.get(where={"document_id": document_id}, limit=1)
            ids = result.get("ids") or []
            return len(ids) > 0
        except Exception as exc:
            logger.warning("Index check failed: %s", exc)
            return False

    def add_documents(self, chunks: List[Document]) -> int:
        if not chunks:
            return 0
        store = self.get_store()
        try:
            store.add_documents(chunks)
            return len(chunks)
        except Exception as exc:
            logger.exception("Failed to add documents to Chroma")
            raise VectorStoreError(f"Vector store write failed: {exc}") from exc

    def delete_by_document_id(self, document_id: str) -> None:
        store = self.get_store()
        try:
            store.delete(where={"document_id": document_id})
            logger.info("Deleted vectors for document_id=%s", document_id)
        except Exception as exc:
            logger.exception("Vector delete failed")
            raise VectorStoreError(f"Vector store delete failed: {exc}") from exc

    def similarity_search_with_score(
        self, query: str, k: int = 5
    ) -> List[Tuple[Document, float]]:
        store = self.get_store()
        try:
            return store.similarity_search_with_score(query, k=k)
        except Exception as exc:
            logger.exception("Similarity search failed")
            raise VectorStoreError(f"Retrieval failed: {exc}") from exc
