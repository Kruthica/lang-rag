from contextlib import asynccontextmanager
import asyncio
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import ask, documents, health, upload
from app.core.config import get_settings
from app.core.logging_config import setup_logging, get_logger
from app.services.embedding_service import get_embeddings
from app.utils.file_utils import ensure_dir

setup_logging()
logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    ensure_dir(Path(settings.upload_dir))
    ensure_dir(Path(settings.chroma_db_dir))
    await asyncio.to_thread(get_embeddings)
    logger.info("RAG backend started — upload_dir=%s chroma=%s", settings.upload_dir, settings.chroma_db_dir)
    yield
    logger.info("RAG backend shutdown")


app = FastAPI(
    title="Production RAG API",
    description="Upload PDFs, embed with Gemini, chat with grounded answers.",
    version="1.0.0",
    lifespan=lifespan,
)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=r"https://[a-zA-Z0-9-]+\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(upload.router)
app.include_router(ask.router)
app.include_router(documents.router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "code": "internal_error"},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
