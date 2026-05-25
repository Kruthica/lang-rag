"""
Load PDF files and produce LangChain Document objects with metadata.

Uses PyPDFLoader from langchain_community; corrupted or encrypted PDFs raise
clear exceptions for the API layer to surface to clients.
"""

from pathlib import Path
from typing import List

from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader

from app.core.logging_config import get_logger
from app.utils.text_cleaner import clean_text

logger = get_logger(__name__)


class PDFLoadError(Exception):
    """Raised when a PDF cannot be read or parsed."""


def load_pdf(path: Path, document_id: str, filename: str) -> List[Document]:
    """
    Extract text per page and attach metadata for chunking/retrieval.

    Metadata keys:
      - source: original filename
      - document_id: registry UUID
      - page: 1-based page number
    """
    if not path.exists():
        raise PDFLoadError(f"File not found: {path}")

    if path.suffix.lower() != ".pdf":
        raise PDFLoadError("Only PDF files are supported")

    try:
        loader = PyPDFLoader(str(path))
        pages = loader.load()
    except Exception as exc:
        logger.exception("Failed to load PDF %s", path)
        raise PDFLoadError(f"Could not read PDF (corrupted or unsupported): {exc}") from exc

    if not pages:
        raise PDFLoadError("PDF contains no extractable text")

    documents: List[Document] = []
    for doc in pages:
        page_num = doc.metadata.get("page", 0)
        # PyPDFLoader uses 0-based page index in metadata
        page_display = int(page_num) + 1 if page_num is not None else None

        cleaned = clean_text(doc.page_content)
        if not cleaned:
            continue

        documents.append(
            Document(
                page_content=cleaned,
                metadata={
                    "source": filename,
                    "document_id": document_id,
                    "page": page_display,
                    "file_path": str(path),
                },
            )
        )

    if not documents:
        raise PDFLoadError("PDF has no readable text after cleaning")

    logger.info("Loaded %d pages from %s", len(documents), filename)
    return documents
