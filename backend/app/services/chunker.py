"""
Split documents into overlapping chunks for embedding.

RecursiveCharacterTextSplitter tries natural separators (paragraphs, sentences)
before hard splits — better semantic boundaries than fixed windows.
"""

from typing import List
from uuid import uuid4

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.logging_config import get_logger

logger = get_logger(__name__)

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


def chunk_documents(documents: List[Document]) -> List[Document]:
    """Split page-level documents into smaller chunks with preserved metadata."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = splitter.split_documents(documents)

    for chunk in chunks:
        # Stable chunk id for deduplication / deletion filters
        chunk.metadata["chunk_id"] = str(uuid4())

    logger.info("Created %d chunks from %d page docs", len(chunks), len(documents))
    return chunks
