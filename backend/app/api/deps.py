"""FastAPI dependencies — shared service instances."""

from functools import lru_cache

from app.services.ingest_service import IngestService
from app.services.rag_service import RAGService
from app.services.vector_store import VectorStoreService


@lru_cache
def get_vector_store_service() -> VectorStoreService:
    return VectorStoreService()


@lru_cache
def get_ingest_service() -> IngestService:
    return IngestService()


@lru_cache
def get_rag_service() -> RAGService:
    return RAGService()
