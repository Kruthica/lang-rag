"""
End-to-end ingestion: save PDF → load → chunk → embed → Chroma + registry.
"""

import asyncio
import hashlib
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

    async def save_upload(self, file: UploadFile) -> Tuple[Path, str]:
        """Stream a size-limited PDF to disk and return its path and digest."""
        original = Path((file.filename or "document.pdf").replace("\\", "/")).name
        if not original.lower().endswith(".pdf"):
            raise PDFLoadError("Only PDF files are allowed")

        content_type = (file.content_type or "").lower().split(";", 1)[0].strip()
        if content_type not in {"", "application/pdf", "application/octet-stream"}:
            raise PDFLoadError("The uploaded file must have PDF content type")

        destination = self.upload_dir / f"{uuid.uuid4()}_{original}"
        digest = hashlib.sha256()
        header = bytearray()
        total_size = 0
        try:
            with destination.open("wb") as output:
                while chunk := await file.read(1024 * 1024):
                    total_size += len(chunk)
                    if total_size > self.settings.max_upload_size_bytes:
                        raise PDFLoadError(
                            "File exceeds the configured "
                            f"{self.settings.max_upload_size_bytes}-byte limit"
                        )
                    if len(header) < 1024:
                        header.extend(chunk[: 1024 - len(header)])
                    digest.update(chunk)
                    output.write(chunk)

            if total_size == 0:
                raise PDFLoadError("The uploaded PDF is empty")
            if b"%PDF-" not in header:
                raise PDFLoadError("The uploaded file is not a valid PDF")
        except Exception:
            destination.unlink(missing_ok=True)
            raise

        logger.info("Saved upload to %s", destination)
        return destination, digest.hexdigest()

    def ingest_file(self, path: Path, filename: str) -> Tuple[str, int]:
        """
        Process one PDF on disk. Returns (document_id, chunk_count).
        """
        doc_id = path.name.split("_", 1)[0] if "_" in path.name else str(uuid.uuid4())

        if self.vector_store.document_already_indexed(doc_id):
            logger.info("Document %s already indexed, skipping", doc_id)
            return doc_id, 0

        pages = load_pdf(path, document_id=doc_id, filename=filename)
        chunks = chunk_documents(pages)
        count = self.vector_store.add_documents(chunks)

        return doc_id, count

    def _find_existing_by_hash(self, content_hash: str) -> dict | None:
        """Return a registry record for identical file content, if present."""
        for record in load_registry(self.upload_dir):
            if record.get("content_hash") == content_hash:
                return record
            stored_path = record.get("stored_path")
            if stored_path and Path(stored_path).is_file():
                digest = hashlib.sha256()
                with Path(stored_path).open("rb") as source:
                    for chunk in iter(lambda: source.read(1024 * 1024), b""):
                        digest.update(chunk)
                if digest.hexdigest() == content_hash:
                    return record
        return None

    async def process_upload(self, file: UploadFile) -> Tuple[str, str, int]:
        """Save and ingest a single uploaded file."""
        original = Path((file.filename or "document.pdf").replace("\\", "/")).name
        path, content_hash = await self.save_upload(file)
        doc_id = path.name.split("_", 1)[0]
        try:
            duplicate = self._find_existing_by_hash(content_hash)
            if duplicate and self.vector_store.document_already_indexed(
                duplicate["id"]
            ):
                path.unlink(missing_ok=True)
                logger.info("Skipping duplicate content upload: %s", original)
                return duplicate["id"], duplicate.get("filename", original), int(
                    duplicate.get("chunk_count", 0)
                )

            _, count = await asyncio.to_thread(self.ingest_file, path, original)
            add_document_record(
                self.upload_dir,
                filename=original,
                stored_path=str(path),
                chunk_count=count,
                document_id=doc_id,
                content_hash=content_hash,
            )
            return doc_id, original, count
        except Exception:
            try:
                self.vector_store.delete_by_document_id(doc_id)
            except Exception:
                logger.exception("Could not roll back vectors for %s", doc_id)
            path.unlink(missing_ok=True)
            raise
