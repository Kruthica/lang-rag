"""Persistent lightweight vector store for memory-constrained deployments."""

import json
import math
import os
import threading
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from app.core.config import Settings, get_settings
from app.core.logging_config import get_logger
from app.services.embedding_service import get_embeddings

logger = get_logger(__name__)
_STORE_LOCK = threading.RLock()


class VectorStoreError(Exception):
    """Raised when vector data cannot be read, written, or queried."""


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
            if not isinstance(data, list):
                raise ValueError("vector store root must be a list")
            for record in data:
                if (
                    not isinstance(record, dict)
                    or not isinstance(record.get("content"), str)
                    or not isinstance(record.get("metadata"), dict)
                    or not isinstance(record.get("vector"), list)
                    or not record["vector"]
                    or not all(
                        isinstance(value, (int, float))
                        and math.isfinite(value)
                        for value in record["vector"]
                    )
                ):
                    raise ValueError("vector store contains an invalid record")
            return data
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            logger.exception("Could not load vector store")
            raise VectorStoreError("Persistent vector data is unreadable") from exc

    def _save(self) -> None:
        temporary = self.store_path.with_suffix(".tmp")
        try:
            with temporary.open("w", encoding="utf-8") as output:
                json.dump(self._records, output, ensure_ascii=False)
                output.flush()
                os.fsync(output.fileno())
            temporary.replace(self.store_path)
        except OSError as exc:
            logger.exception("Could not persist vector store")
            raise VectorStoreError("Could not save document vectors") from exc
        finally:
            temporary.unlink(missing_ok=True)

    def document_already_indexed(self, document_id: str) -> bool:
        with _STORE_LOCK:
            self._records = self._load()
            return any(
                record["metadata"].get("document_id") == document_id
                for record in self._records
            )

    def has_documents(self) -> bool:
        with _STORE_LOCK:
            self._records = self._load()
            return bool(self._records)

    def add_documents(self, chunks: List[Document]) -> int:
        if not chunks:
            return 0
        try:
            vectors = self.embeddings.embed_documents(
                [chunk.page_content for chunk in chunks]
            )
            if len(vectors) != len(chunks) or not vectors:
                raise ValueError("Embedding provider returned an invalid vector count")
            dimensions = len(vectors[0])
            if not dimensions or any(
                len(vector) != dimensions
                or not all(math.isfinite(value) for value in vector)
                for vector in vectors
            ):
                raise ValueError("Embedding provider returned invalid vectors")
            additions = [
                {
                    "content": chunk.page_content,
                    "metadata": dict(chunk.metadata),
                    "vector": vector,
                }
                for chunk, vector in zip(chunks, vectors)
            ]
            with _STORE_LOCK:
                self._records = self._load()
                self._records.extend(additions)
                self._save()
            return len(chunks)
        except VectorStoreError:
            raise
        except Exception as exc:
            logger.exception("Failed to generate or persist document vectors")
            raise VectorStoreError("Could not index document content") from exc

    def delete_by_document_id(self, document_id: str) -> None:
        with _STORE_LOCK:
            self._records = self._load()
            self._records = [
                record
                for record in self._records
                if record["metadata"].get("document_id") != document_id
            ]
            self._save()
        logger.info("Deleted vectors for document_id=%s", document_id)

    def similarity_search_with_score(
        self, query: str, k: int = 5
    ) -> List[Tuple[Document, float]]:
        if k <= 0:
            return []
        try:
            query_vector = self.embeddings.embed_query(query)
            if not query_vector or not all(
                math.isfinite(value) for value in query_vector
            ):
                raise ValueError("Embedding provider returned an invalid query vector")
            with _STORE_LOCK:
                self._records = self._load()
                records = list(self._records)
            scored = []
            for record in records:
                score = self._cosine_similarity(query_vector, record["vector"])
                if score is None:
                    logger.warning(
                        "Skipping vector with incompatible dimensions for document %s",
                        record["metadata"].get("document_id"),
                    )
                    continue
                scored.append(
                    (
                        Document(
                            page_content=record["content"],
                            metadata=record["metadata"],
                        ),
                        score,
                    )
                )
            scored.sort(key=lambda item: item[1], reverse=True)
            return scored[:k]
        except VectorStoreError:
            raise
        except Exception as exc:
            logger.exception("Vector similarity search failed")
            raise VectorStoreError("Could not search indexed documents") from exc

    @staticmethod
    def _cosine_similarity(
        first: List[float], second: List[float]
    ) -> Optional[float]:
        if len(first) != len(second):
            return None
        numerator = sum(left * right for left, right in zip(first, second))
        first_norm = math.sqrt(sum(value * value for value in first))
        second_norm = math.sqrt(sum(value * value for value in second))
        denominator = first_norm * second_norm
        return numerator / denominator if denominator else 0.0
