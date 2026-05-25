"""
Normalize raw PDF text before chunking.

PDF extractors often emit broken whitespace, hyphenation artifacts, and
control characters — cleaning improves retrieval quality.
"""

import re
import unicodedata


def clean_text(text: str) -> str:
    """Return normalized plain text suitable for splitting."""
    if not text:
        return ""

    # Unicode normalization (e.g. ligatures)
    text = unicodedata.normalize("NFKC", text)

    # Remove null bytes and most control chars (keep newlines/tabs)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", " ", text)

    # Fix hyphenation across line breaks: "exam-\nple" -> "example"
    text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)

    # Collapse excessive whitespace but preserve paragraph breaks
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()
