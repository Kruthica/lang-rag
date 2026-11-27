from typing import List

from fastapi import APIRouter, File, UploadFile

from app.api.deps import get_ingest_service
from app.core.logging_config import get_logger
from app.models.schemas import UploadResponse, UploadResultItem
from app.services.ingest_service import IngestService
from app.services.pdf_loader import PDFLoadError
from app.services.vector_store import VectorStoreError

router = APIRouter(tags=["upload"])
logger = get_logger(__name__)


@router.post("/upload", response_model=UploadResponse)
async def upload_documents(
    files: List[UploadFile] = File(...),
) -> UploadResponse:
    """
    Upload one or more PDFs and report each file's indexing result.
    """
    ingest: IngestService = get_ingest_service()
    uploaded: List[UploadResultItem] = []
    skipped: List[str] = []

    for file in files:
        name = file.filename or "unknown.pdf"
        try:
            doc_id, filename, count = await ingest.process_upload(file)
            uploaded.append(
                UploadResultItem(
                    document_id=doc_id,
                    filename=filename,
                    chunk_count=count,
                    message=f"Indexed {count} chunks",
                )
            )
        except PDFLoadError as exc:
            logger.warning("Upload skipped for %s: %s", name, exc)
            skipped.append(f"{name}: {exc}")
        except VectorStoreError:
            logger.exception("Indexing failed for %s", name)
            skipped.append(f"{name}: Could not index this PDF. Please try again.")
        except Exception:
            logger.exception("Upload failed for %s", name)
            skipped.append(f"{name}: Processing failed. Please try again.")

    return UploadResponse(uploaded=uploaded, skipped=skipped)
