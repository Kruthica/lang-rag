"""API schemas — separate from internal service types for stable contracts."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"
    gemini_configured: bool


class SourceChunk(BaseModel):
    content: str
    filename: str
    page: Optional[int] = None
    score: float = Field(description="Similarity confidence 0–1 (higher is better)")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class UploadResultItem(BaseModel):
    document_id: str
    filename: str
    chunk_count: int
    message: str


class UploadResponse(BaseModel):
    uploaded: List[UploadResultItem]
    skipped: List[str] = Field(default_factory=list)


class DocumentInfo(BaseModel):
    id: str
    filename: str
    chunk_count: int
    uploaded_at: str


class DocumentsListResponse(BaseModel):
    documents: List[DocumentInfo]


class ChatMessage(BaseModel):
    role: str = Field(description="'user' or 'assistant'")
    content: str


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=8000)
    history: List[ChatMessage] = Field(default_factory=list)
    stream: bool = False


class AskResponse(BaseModel):
    answer: str
    sources: List[SourceChunk]
    session_id: Optional[str] = None


class ErrorResponse(BaseModel):
    detail: str
    code: Optional[str] = None
