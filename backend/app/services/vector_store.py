"""Persistent lightweight vector store for memory-constrained deployments."""

import json
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from app.core.config import Settings, get_settings
from app.core.logging_config import get_logger
from app.services.embedding_service import get_embeddings

logger = get_logger(__name__)


class VectorStoreError(Exception):
    pass


class VectorStoreService:
    """Persist document chunks and vectors without a native database process."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self.persist_dir = Path(self.settings.chroma_db_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.store_path = self.persist_dir / "vectors.json"
        self._records: List[Dict] = self._load()

    @property
    def embeddings(self) -> Embeddings:
        return get_embeddings()

    def _load(self) -> List[Dict]:
        if not self.store_path.exists():
            return []
        try:
            data = json.loads(self.store_path.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Could not load vector store: %s", exc)
            return []

    def _save(self) -> None:
        temporary = self.store_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(self._records), encoding="utf-8")
        temporary.replace(self.store_path)

    def document_already_indexed(self, document_id: str) -> bool:
        self._records = self._load()
        return any(
            record.get("metadata", {}).get("document_id") == document_id
            for record in self._records
        )

    def add_documents(self, chunks: List[Document]) -> int:
        if not chunks:
            return 0
        try:
            vectors = self.embeddings.embed_documents(
                [chunk.page_content for chunk in chunks]
            )
            self._records.extend(
                {
                    "content": chunk.page_content,
                    "metadata": chunk.metadata,
                    "vector": vector,
                }
                for chunk, vector in zip(chunks, vectors)
            )
            self._save()
            return len(chunks)
        except (OSError, TypeError, ValueError) as exc:
            logger.exception("Failed to persist vectors")
            raise VectorStoreError(f"Vector store write failed: {exc}") from exc

    def delete_by_document_id(self, document_id: str) -> None:
        self._records = [
            record
            for record in self._records
            if record.get("metadata", {}).get("document_id") != document_id
        ]
        self._save()
        logger.info("Deleted vectors for document_id=%s", document_id)

    def similarity_search_with_score(
        self, query: str, k: int = 5
    ) -> List[Tuple[Document, float]]:
        self._records = self._load()
        query_vector = self.embeddings.embed_query(query)
        scored = [
            (
                Document(
                    page_content=record["content"],
                    metadata=record.get("metadata", {}),
                ),
                self._cosine_similarity(query_vector, record["vector"]),
            )
            for record in self._records
        ]
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[:k]

    @staticmethod
    def _cosine_similarity(first: List[float], second: List[float]) -> float:
        if len(first) != len(second):
            return 0.0
        numerator = sum(left * right for left, right in zip(first, second))
        first_norm = math.sqrt(sum(value * value for value in first))
        second_norm = math.sqrt(sum(value * value for value in second))
        denominator = first_norm * second_norm
        return numerator / denominator if denominator else 0.0
