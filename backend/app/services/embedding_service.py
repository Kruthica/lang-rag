"""Embedding model factory with a process-wide cache."""

import hashlib
import re
from functools import lru_cache
from math import sqrt
from typing import List

from langchain_core.embeddings import Embeddings
from app.core.config import get_settings


class HashEmbeddings(Embeddings):
    """Small dependency-free fallback suitable for memory-constrained hosts."""

    dimensions = 384

    def _embed(self, text: str) -> List[float]:
        vector = [0.0] * self.dimensions
        tokens = re.findall(r"\w+", text.lower())
        for token in tokens:
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] & 1 else -1.0
            vector[index] += sign
        magnitude = sqrt(sum(value * value for value in vector))
        return [value / magnitude for value in vector] if magnitude else vector

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._embed(text)


@lru_cache(maxsize=1)
def get_embeddings():
    settings = get_settings()
    if settings.embedding_provider.lower() == "huggingface":
        from langchain_community.embeddings import HuggingFaceEmbeddings

        return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    return HashEmbeddings()