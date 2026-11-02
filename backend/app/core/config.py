"""
Application settings loaded from environment variables.

Uses pydantic-settings so values can come from a .env file next to the backend
or from the process environment (Docker-friendly).
"""

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# Resolve backend directory (parent of `app/`) for default relative paths
_BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Central typed configuration — avoids magic strings scattered in code."""
    hf_token: str = Field(default="", validation_alias="HF_TOKEN")
    hf_model: str = Field(
        default="meta-llama/Meta-Llama-3.1-8B-Instruct",
        validation_alias="HF_MODEL",
    )
    model_config = SettingsConfigDict(
        env_file=str(_BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    chroma_db_dir: str = Field(
        default=str(_BACKEND_DIR / "vectorstore"),
        validation_alias="CHROMA_DB_DIR",
    )
    upload_dir: str = Field(
        default=str(_BACKEND_DIR / "uploads"),
        validation_alias="UPLOAD_DIR",
    )
    embedding_provider: str = Field(
        default="hash",
        validation_alias="EMBEDDING_PROVIDER",
    )
    cors_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173,https://lang-rag-git-main-kruthicas-projects.vercel.app",
        validation_alias="CORS_ORIGINS",
    )
    llm_timeout_seconds: float = Field(
        default=120.0,
        validation_alias="LLM_TIMEOUT_SECONDS",
    )
    collection_name: str = Field(
        default="rag_documents",
        validation_alias="CHROMA_COLLECTION_NAME",
    )

    @property
    def cors_origin_list(self) -> List[str]:
        raw = (self.cors_origins or "").strip()
        if raw == "*":
            return ["*"]
        return [o.strip() for o in raw.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton for dependency injection."""
    return Settings()
