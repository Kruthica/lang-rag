"""Filesystem helpers for uploads and document registry."""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.logging_config import get_logger

logger = get_logger(__name__)

REGISTRY_FILENAME = "documents_registry.json"


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def registry_path(upload_dir: Path) -> Path:
    return upload_dir / REGISTRY_FILENAME


def load_registry(upload_dir: Path) -> List[Dict[str, Any]]:
    path = registry_path(upload_dir)
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Could not read document registry: %s", exc)
        return []


def save_registry(upload_dir: Path, records: List[Dict[str, Any]]) -> None:
    ensure_dir(upload_dir)
    path = registry_path(upload_dir)
    with path.open("w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, default=str)


def add_document_record(
    upload_dir: Path,
    filename: str,
    stored_path: str,
    chunk_count: int,
    document_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Append a document entry and return the new record."""
    records = load_registry(upload_dir)
    doc_id = document_id or str(uuid.uuid4())
    record = {
        "id": doc_id,
        "filename": filename,
        "stored_path": stored_path,
        "chunk_count": chunk_count,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    }
    records.append(record)
    save_registry(upload_dir, records)
    return record


def remove_document_record(upload_dir: Path, doc_id: str) -> Optional[Dict[str, Any]]:
    records = load_registry(upload_dir)
    removed = None
    kept: List[Dict[str, Any]] = []
    for r in records:
        if r.get("id") == doc_id:
            removed = r
        else:
            kept.append(r)
    if removed:
        save_registry(upload_dir, kept)
    return removed


def get_document_record(upload_dir: Path, doc_id: str) -> Optional[Dict[str, Any]]:
    for r in load_registry(upload_dir):
        if r.get("id") == doc_id:
            return r
    return None
