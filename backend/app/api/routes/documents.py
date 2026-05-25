from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.api.deps import get_vector_store_service
from app.core.config import get_settings
from app.core.logging_config import get_logger
from app.models.schemas import DocumentInfo, DocumentsListResponse
from app.services.vector_store import VectorStoreError, VectorStoreService
from app.utils.file_utils import load_registry, remove_document_record

router = APIRouter(tags=["documents"])
logger = get_logger(__name__)


@router.get("/documents", response_model=DocumentsListResponse)
async def list_documents() -> DocumentsListResponse:
    settings = get_settings()
    upload_dir = Path(settings.upload_dir)
    records = load_registry(upload_dir)
    docs = [
        DocumentInfo(
            id=r["id"],
            filename=r.get("filename", "unknown"),
            chunk_count=int(r.get("chunk_count", 0)),
            uploaded_at=r.get("uploaded_at", ""),
        )
        for r in records
    ]
    return DocumentsListResponse(documents=docs)


@router.delete("/documents/{document_id}")
async def delete_document(document_id: str) -> dict:
    settings = get_settings()
    upload_dir = Path(settings.upload_dir)
    record = remove_document_record(upload_dir, document_id)

    if not record:
        raise HTTPException(status_code=404, detail="Document not found")

    # Remove vectors from Chroma
    vector_store: VectorStoreService = get_vector_store_service()
    try:
        vector_store.delete_by_document_id(document_id)
    except VectorStoreError as exc:
        logger.error("Vector delete error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    # Remove file from disk
    stored = record.get("stored_path")
    if stored:
        path = Path(stored)
        if path.exists():
            try:
                path.unlink()
            except OSError as exc:
                logger.warning("Could not delete file %s: %s", path, exc)

    return {"status": "deleted", "id": document_id}
