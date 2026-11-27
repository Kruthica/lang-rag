"""
Load PDF files and produce LangChain Document objects with metadata.

Uses PyPDFLoader from langchain_community; corrupted or encrypted PDFs raise
clear exceptions for the API layer to surface to clients.
"""

from pathlib import Path
from typing import List

from langchain_core.documents import Document
from pypdf import PdfReader

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
        raise PDFLoadError("Uploaded PDF could not be found during processing")

    if path.suffix.lower() != ".pdf":
        raise PDFLoadError("Only PDF files are supported")

    try:
        reader = PdfReader(str(path))
        if reader.is_encrypted:
            raise PDFLoadError("Password-protected PDFs are not supported")
        if not reader.pages:
            raise PDFLoadError("PDF contains no pages")

        pages = []
        for page_number, page in enumerate(reader.pages, start=1):
            page_text = page.extract_text() or ""
            cleaned = clean_text(page_text)
            if cleaned:
                pages.append(
                    Document(
                        page_content=cleaned,
                        metadata={
                            "source": filename,
                            "page": page_number,
                        },
                    )
                )
    except PDFLoadError:
        raise
    except Exception as exc:
        logger.exception("Failed to load PDF %s", path)
        raise PDFLoadError(
            "Could not read this PDF. It may be corrupted or use unsupported encryption."
        ) from exc

    if not pages:
        raise PDFLoadError("PDF contains no extractable text")

    documents: List[Document] = []
    for doc in pages:
        documents.append(
            Document(
                page_content=doc.page_content,
                metadata={
                    "source": filename,
                    "document_id": document_id,
                    "page": doc.metadata["page"],
                    "file_path": str(path),
                },
            )
        )

    logger.info("Loaded %d pages from %s", len(documents), filename)
    return documents
