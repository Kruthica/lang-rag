# Production RAG System

A full-stack **Retrieval-Augmented Generation (RAG)** application: upload PDFs, embed with **Google Gemini**, store vectors in **ChromaDB**, and chat with grounded answers and source citations.

## Features

- Modern dark chat UI (React, Tailwind, Framer Motion)
- PDF upload (drag & drop, multiple files, progress)
- PDF ingestion with PyPDFLoader and text cleaning
- Chunking (1000 / 200 overlap) with metadata (filename, page)
- Gemini embeddings + ChromaDB persistence
- Top-5 similarity retrieval with confidence scores
- Gemini 2.0 Flash grounded answers
- Conversational history for follow-ups
- Streaming responses (SSE)
- Markdown + syntax highlighting, copy/regenerate/clear chat
- Docker Compose deployment

## Project structure

```
lang-rag/
├── backend/          # FastAPI + LangChain + Chroma
├── frontend/         # React + Vite
├── docker-compose.yml
├── .env.example
└── README.md
```

## Prerequisites

- Python 3.11+
- Node.js 20+
- [Google AI API key](https://aistudio.google.com/apikey) for Gemini

## Environment setup

1. Copy the example env file:

```bash
cp .env.example .env
```

2. Set your key in `.env` (or `backend/.env` for local backend runs):

```
GEMINI_API_KEY=your_key_here
```

## Run locally (development)

### Backend

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API docs: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — Vite proxies `/api` to the backend.

## Docker

From the project root (with `.env` containing `GEMINI_API_KEY`):

```bash
docker compose up --build
```

- Frontend: http://localhost
- Backend: http://localhost:8000

## API examples

### Health

```bash
curl http://localhost:8000/health
```

### Upload PDFs

```bash
curl -X POST http://localhost:8000/upload \
  -F "files=@./sample.pdf"
```

### Ask (JSON)

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d "{\"question\": \"What is this document about?\", \"history\": []}"
```

### List documents

```bash
curl http://localhost:8000/documents
```

### Delete document

```bash
curl -X DELETE http://localhost:8000/documents/{document_id}
```

### Streaming

```bash
curl -N -X POST http://localhost:8000/ask/stream \
  -H "Content-Type: application/json" \
  -d "{\"question\": \"Summarize key points\", \"history\": []}"
```

## Screenshots

_Add screenshots of the chat UI and source cards after your first run._

## Future improvements

- Multi-user sessions and authentication
- PostgreSQL for metadata, Redis for caching
- Hybrid search + reranking
- OCR and image understanding
- Voice input and analytics dashboard

## License

MIT — use freely for learning and production prototypes.
