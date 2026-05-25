"""
Format conversational history for the RAG prompt.

We keep a lightweight in-request history (from the client) rather than server
sessions — simple for single-user dev; swap for Redis/DB for multi-user prod.
"""

from typing import List

from app.models.schemas import ChatMessage

MAX_HISTORY_TURNS = 6


def format_history(history: List[ChatMessage]) -> str:
    """Build a compact transcript for follow-up questions."""
    if not history:
        return ""

    # Only keep the most recent turns to limit prompt size
    recent = history[-MAX_HISTORY_TURNS * 2 :]
    lines: List[str] = []
    for msg in recent:
        role = msg.role.strip().lower()
        if role not in ("user", "assistant"):
            continue
        label = "User" if role == "user" else "Assistant"
        lines.append(f"{label}: {msg.content.strip()}")

    if not lines:
        return ""

    return "Previous conversation:\n" + "\n".join(lines) + "\n\n"
