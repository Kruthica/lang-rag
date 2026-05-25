"""
End-to-end ingestion: save PDF → load → chunk → embed → Chroma + registry.
"""

import uuid
from pathlib import Path
from typing import List, Tuple

from fastapi import UploadFile

from app.core.config import Settings, get_settings
from app.core.logging_config import get_logger
from app.services.chunker import chunk_documents
from app.services.pdf_loader import PDFLoadError, load_pdf
from app.services.vector_store import VectorStoreService
from app.utils.file_utils import add_document_record, ensure_dir, load_registry

logger = get_logger(__name__)


class IngestService:
    def __init__(
        self,
        settings: Settings | None = None,
        vector_store: VectorStoreService | None = None,
    ):
        self.settings = settings or get_settings()
        self.upload_dir = Path(self.settings.upload_dir)
        ensure_dir(self.upload_dir)
        self.vector_store = vector_store or VectorStoreService(self.settings)

    async def save_upload(self, file: UploadFile) -> Path:
        """Persist raw bytes under uploads/ with a unique name."""
        original = Path(file.filename or "document.pdf").name
        if not original.lower().endswith(".pdf"):
            raise PDFLoadError("Only PDF files are allowed")

        doc_id = str(uuid.uuid4())
        safe_name = f"{doc_id}_{original}"
        dest = self.upload_dir / safe_name

        content = await file.read()
        if len(content) == 0:
            raise PDFLoadError("Empty file")

        if len(content) > 50 * 1024 * 1024:
            raise PDFLoadError("File exceeds 50MB limit")

        dest.write_bytes(content)
        logger.info("Saved upload to %s", dest)
        return dest

    def ingest_file(self, path: Path, filename: str) -> Tuple[str, int]:
        """
        Process one PDF on disk. Returns (document_id, chunk_count).
        Skips re-embedding if document_id already indexed (by filename hash check done via new uuid each time —
        dedup is per upload id stored in registry).
        """
        doc_id = path.name.split("_", 1)[0] if "_" in path.name else str(uuid.uuid4())

        if self.vector_store.document_already_indexed(doc_id):
            logger.info("Document %s already indexed, skipping", doc_id)
            return doc_id, 0

        pages = load_pdf(path, document_id=doc_id, filename=filename)
        chunks = chunk_documents(pages)
        count = self.vector_store.add_documents(chunks)

        add_document_record(
            self.upload_dir,
            filename=filename,
            stored_path=str(path),
            chunk_count=count,
            document_id=doc_id,
        )
        return doc_id, count

    def _find_existing_by_filename(self, filename: str) -> str | None:
        """Return document_id if this filename was already indexed (avoid duplicate embeddings)."""
        for record in load_registry(self.upload_dir):
            if record.get("filename") == filename:
                return record.get("id")
        return None

    async def process_upload(self, file: UploadFile) -> Tuple[str, str, int]:
        """Save and ingest a single uploaded file."""
        original = Path(file.filename or "document.pdf").name
        existing_id = self._find_existing_by_filename(original)
        if existing_id and self.vector_store.document_already_indexed(existing_id):
            logger.info("Skipping duplicate upload: %s", original)
            record = next(
                (r for r in load_registry(self.upload_dir) if r.get("id") == existing_id),
                {},
            )
            return existing_id, original, int(record.get("chunk_count", 0))

        path = await self.save_upload(file)
        doc_id, count = self.ingest_file(path, original)
        return doc_id, original, count
