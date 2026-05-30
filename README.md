# Lang-RAG

A production-ready Retrieval-Augmented Generation (RAG) system built with FastAPI, React, ChromaDB, and Hugging Face embeddings. Upload PDF documents, index them into a vector database, and interact with them through a conversational AI interface with source-grounded responses.

---

## Features

### Document Management

* Upload single or multiple PDF documents
* Automatic PDF text extraction
* Document listing and deletion
* Persistent document storage

### RAG Pipeline

* PDF parsing and text cleaning
* Intelligent text chunking with overlap
* Hugging Face sentence-transformer embeddings
* ChromaDB vector storage and retrieval
* Metadata-aware document indexing

### Conversational AI

* Context-aware question answering
* Source-grounded responses
* Conversation history support
* Streaming responses using Server-Sent Events (SSE)
* Confidence-based document retrieval

### Modern Frontend

* React + Vite
* Responsive UI
* Drag-and-drop file uploads
* Real-time chat interface
* Markdown rendering
* Syntax highlighting
* Upload progress tracking

### Deployment Ready

* FastAPI backend
* Vercel frontend deployment
* Render backend deployment
* Docker support
* Environment-based configuration

---

## Tech Stack

### Backend

* FastAPI
* LangChain
* ChromaDB
* Sentence Transformers
* Hugging Face Embeddings
* PyPDF
* Uvicorn

### Frontend

* React
* Vite
* Axios
* Tailwind CSS
* Framer Motion

### Vector Database

* ChromaDB

---

## Project Structure

```text
lang-rag/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── services/
│   │   └── utils/
│   │
│   ├── uploads/
│   ├── vectorstore/
│   ├── requirements.txt
│   └── main.py
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.js
│
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Installation

### Clone Repository

```bash
git clone https://github.com/Kruthica/lang-rag.git
cd lang-rag
```

---

## Backend Setup

```bash
cd backend

python -m venv .venv
```

### Activate Environment

Windows:

```bash
.venv\Scripts\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configure Environment

Create a `.env` file inside the backend folder:

```env
HF_TOKEN=your_huggingface_token

UPLOAD_DIR=uploads
CHROMA_DB_DIR=vectorstore

CORS_ORIGINS=http://localhost:5173,http://localhost:5174
```

### Run Backend

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend API:

```text
http://localhost:8000
```

Swagger Documentation:

```text
http://localhost:8000/docs
```

---

## Frontend Setup

```bash
cd frontend

npm install
npm run dev
```

Frontend:

```text
http://localhost:5173
```

---

## API Endpoints

### Health Check

```http
GET /health
```

### Upload Documents

```http
POST /upload
```

### Ask Questions

```http
POST /ask
```

### Streaming Answers

```http
POST /ask/stream
```

### List Documents

```http
GET /documents
```

### Delete Document

```http
DELETE /documents/{document_id}
```

---

## Example Requests

### Upload PDF

```bash
curl -X POST http://localhost:8000/upload \
-F "files=@sample.pdf"
```

### Ask Question

```bash
curl -X POST http://localhost:8000/ask \
-H "Content-Type: application/json" \
-d '{
  "question":"Summarize this document",
  "history":[]
}'
```

### Get Documents

```bash
curl http://localhost:8000/documents
```

---

## Deployment

### Frontend (Vercel)

Set:

```env
VITE_API_URL=https://your-backend-url.onrender.com
```

Deploy:

```bash
vercel --prod
```

### Backend (Render)

Set environment variables:

```env
HF_TOKEN=your_token
```

Start command:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

---

## Future Improvements

* Hybrid search (vector + keyword)
* Reranking pipelines
* OCR support for scanned PDFs
* Multi-user authentication
* Role-based document access
* Citation highlighting
* Document collections and folders
* Voice-based interactions

---

## License

MIT License

---

## Author

**Kruthica**

Built as a production-focused Retrieval-Augmented Generation system for document intelligence and conversational knowledge retrieval.
