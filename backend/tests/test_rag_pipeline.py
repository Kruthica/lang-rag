import asyncio
import io
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import FastAPI, UploadFile
from fastapi.testclient import TestClient
from langchain_core.documents import Document
from pypdf import PdfWriter
from starlette.datastructures import Headers

from app.core.config import Settings
from app.api.routes import ask, documents, upload
from app.models.schemas import ChatMessage
from app.services.embedding_service import HashEmbeddings
from app.services.ingest_service import IngestService
from app.services.pdf_loader import PDFLoadError, load_pdf
from app.services.rag_service import RAGService
from app.services.vector_store import VectorStoreService
from app.utils.file_utils import load_registry


def make_text_pdf(pages: list[str]) -> bytes:
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        (
            f"<< /Type /Pages /Kids [{' '.join(f'{3 + 2 * i} 0 R' for i in range(len(pages)))}] "
            f"/Count {len(pages)} >>"
        ).encode(),
    ]
    for index, text in enumerate(pages):
        page_id = 3 + 2 * index
        content_id = page_id + 1
        stream = (
            f"BT /F1 12 Tf 50 750 Td ({text}) Tj ET".encode("ascii")
        )
        objects.extend(
            [
                (
                    f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                    f"/Resources << /Font << /F1 {3 + 2 * len(pages)} 0 R >> >> "
                    f"/Contents {content_id} 0 R >>"
                ).encode(),
                b"<< /Length "
                + str(len(stream)).encode()
                + b" >>\nstream\n"
                + stream
                + b"\nendstream",
            ]
        )
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for object_id, body in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{object_id} 0 obj\n".encode())
        pdf.extend(body)
        pdf.extend(b"\nendobj\n")
    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(offsets)}\n".encode())
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode())
    pdf.extend(
        f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n".encode()
    )
    return bytes(pdf)


def upload_file(name: str, content: bytes, content_type: str = "application/pdf"):
    return UploadFile(
        file=io.BytesIO(content),
        filename=name,
        headers=Headers({"content-type": content_type}),
    )


class RagPipelineTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.settings = Settings(
            upload_dir=str(root / "uploads"),
            chroma_db_dir=str(root / "vectors"),
            hf_token="",
        )
        self.embeddings = HashEmbeddings()

    def tearDown(self):
        self.temporary.cleanup()

    def test_hash_embeddings_are_deterministic_and_dimension_compatible(self):
        text = "Paris is the capital of France"
        document_vector = self.embeddings.embed_documents([text])[0]
        query_vector = self.embeddings.embed_query(text)
        self.assertEqual(document_vector, query_vector)
        self.assertEqual(len(document_vector), HashEmbeddings.dimensions)

    def test_upload_extracts_pages_indexes_chunks_and_deduplicates_content(self):
        service = IngestService(self.settings)
        pdf = make_text_pdf(
            ["Paris is the capital of France.", "The Eiffel Tower is in Paris."]
        )
        first_id, filename, chunk_count = asyncio.run(
            service.process_upload(upload_file("facts.pdf", pdf))
        )
        self.assertEqual(filename, "facts.pdf")
        self.assertGreaterEqual(chunk_count, 2)

        pages = load_pdf(
            Path(load_registry(Path(self.settings.upload_dir))[0]["stored_path"]),
            first_id,
            filename,
        )
        self.assertEqual([page.metadata["page"] for page in pages], [1, 2])
        self.assertIn("Paris", pages[0].page_content)

        duplicate_id, _, duplicate_chunks = asyncio.run(
            service.process_upload(upload_file("renamed-copy.pdf", pdf))
        )
        self.assertEqual(first_id, duplicate_id)
        self.assertEqual(chunk_count, duplicate_chunks)
        self.assertEqual(len(load_registry(Path(self.settings.upload_dir))), 1)

        matches = service.vector_store.similarity_search_with_score(
            "capital France Paris", k=2
        )
        self.assertTrue(matches)
        self.assertEqual(matches[0][0].metadata["document_id"], first_id)

    def test_invalid_and_corrupted_pdfs_are_rejected_without_registry_entries(self):
        service = IngestService(self.settings)
        with self.assertRaises(PDFLoadError):
            asyncio.run(service.process_upload(upload_file("not.pdf", b"no pdf")))
        with self.assertRaises(PDFLoadError):
            asyncio.run(
                service.process_upload(
                    upload_file("wrong-type.pdf", b"%PDF-1.4", "text/plain")
                )
            )
        with self.assertRaises(PDFLoadError):
            asyncio.run(
                service.process_upload(
                    upload_file("corrupt.pdf", b"%PDF-this is not a valid PDF")
                )
            )
        self.assertEqual(load_registry(Path(self.settings.upload_dir)), [])
        self.assertEqual(list(Path(self.settings.upload_dir).glob("*.pdf")), [])

    def test_password_protected_and_textless_pdfs_are_rejected(self):
        encrypted_writer = PdfWriter()
        encrypted_writer.add_blank_page(width=200, height=200)
        encrypted_writer.encrypt("secret")
        encrypted_pdf = io.BytesIO()
        encrypted_writer.write(encrypted_pdf)
        encrypted_path = Path(self.temporary.name) / "encrypted.pdf"
        encrypted_path.write_bytes(encrypted_pdf.getvalue())

        with self.assertRaisesRegex(PDFLoadError, "Password-protected"):
            load_pdf(encrypted_path, "encrypted", "encrypted.pdf")

        blank_writer = PdfWriter()
        blank_writer.add_blank_page(width=200, height=200)
        blank_pdf = io.BytesIO()
        blank_writer.write(blank_pdf)
        blank_path = Path(self.temporary.name) / "blank.pdf"
        blank_path.write_bytes(blank_pdf.getvalue())
        with self.assertRaisesRegex(PDFLoadError, "no extractable text"):
            load_pdf(blank_path, "blank", "blank.pdf")

    def test_upload_size_limit_is_enforced_and_partial_file_removed(self):
        self.settings.max_upload_size_bytes = 12
        service = IngestService(self.settings)
        with self.assertRaisesRegex(PDFLoadError, "exceeds"):
            asyncio.run(
                service.process_upload(
                    upload_file("large.pdf", b"%PDF-1.4" + b"x" * 20)
                )
            )
        self.assertEqual(list(Path(self.settings.upload_dir).glob("*.pdf")), [])

    def test_retrieval_only_returns_relevant_context_and_reports_no_match(self):
        store = VectorStoreService(self.settings)
        store.add_documents(
            [
                Document(
                    page_content="The capital of France is Paris.",
                    metadata={"source": "facts.pdf", "document_id": "doc-1", "page": 1},
                )
            ]
        )
        rag = RAGService(self.settings, vector_store=store)
        response = asyncio.run(
            rag.ask("What is the capital of France?", [ChatMessage(role="user", content="Hi")])
        )
        self.assertIn("France", response.answer)
        self.assertTrue(response.sources)

        unrelated = asyncio.run(rag.ask("What is the mass of Jupiter?"))
        self.assertIn("couldn't find relevant information", unrelated.answer)
        self.assertFalse(unrelated.sources)

    def test_vector_data_reloads_and_deletes_across_service_instances(self):
        first_store = VectorStoreService(self.settings)
        first_store.add_documents(
            [
                Document(
                    page_content="A sufficiently useful passage",
                    metadata={"document_id": "doc-2", "source": "two.pdf"},
                )
            ]
        )
        second_store = VectorStoreService(self.settings)
        self.assertTrue(second_store.document_already_indexed("doc-2"))
        second_store.delete_by_document_id("doc-2")
        self.assertFalse(first_store.has_documents())

    def test_multiple_documents_and_followup_history_retrieve_their_sources(self):
        store = VectorStoreService(self.settings)
        store.add_documents(
            [
                Document(
                    page_content="Paris is the capital of France.",
                    metadata={"document_id": "france", "source": "france.pdf", "page": 1},
                ),
                Document(
                    page_content="Berlin is the capital of Germany.",
                    metadata={"document_id": "germany", "source": "germany.pdf", "page": 1},
                ),
            ]
        )
        rag = RAGService(self.settings, vector_store=store)
        comparison, sources = rag.retrieve("Compare the capital cities Paris and Berlin")
        self.assertIn("France", comparison)
        self.assertIn("Germany", comparison)
        self.assertEqual({source.filename for source in sources}, {"france.pdf", "germany.pdf"})

        followup, followup_sources = rag.retrieve(
            "What about Germany?",
            history=[ChatMessage(role="user", content="Tell me the capital of France")],
        )
        self.assertIn("Germany", followup)
        self.assertEqual({source.filename for source in followup_sources}, {"germany.pdf"})

    def test_generation_receives_retrieved_context_and_returns_model_answer(self):
        self.settings.hf_token = "test-token"
        store = VectorStoreService(self.settings)
        store.add_documents(
            [
                Document(
                    page_content="The capital of France is Paris.",
                    metadata={"document_id": "doc", "source": "facts.pdf", "page": 1},
                )
            ]
        )
        rag = RAGService(self.settings, vector_store=store)

        class FakeModel:
            def chat_completion(self, *, model, messages, **kwargs):
                self.asserted_model = model
                self.model = model
                self.messages = messages
                return SimpleNamespace(
                    choices=[
                        SimpleNamespace(
                            message=SimpleNamespace(content="The capital is Paris.")
                        )
                    ]
                )

        fake_model = FakeModel()
        rag._get_llm = lambda: fake_model
        response = asyncio.run(rag.ask("What is the capital of France?"))
        self.assertEqual(response.answer, "The capital is Paris.")
        self.assertEqual(fake_model.asserted_model, "meta-llama/Meta-Llama-3.1-8B-Instruct")
        self.assertIn("The capital of France is Paris.", fake_model.messages[1]["content"])
        self.assertTrue(response.sources)

    def test_api_upload_list_ask_and_stream_contracts(self):
        ingest = IngestService(self.settings)
        rag = RAGService(self.settings)
        app = FastAPI()
        app.include_router(upload.router)
        app.include_router(documents.router)
        app.include_router(ask.router)

        with (
            patch.object(upload, "get_ingest_service", return_value=ingest),
            patch.object(ask, "get_rag_service", return_value=rag),
            patch.object(documents, "get_settings", return_value=self.settings),
            TestClient(app) as client,
        ):
            pdf = make_text_pdf(["The capital of France is Paris."])
            uploaded = client.post(
                "/upload",
                files={"files": ("facts.pdf", pdf, "application/pdf")},
            )
            self.assertEqual(uploaded.status_code, 200)
            self.assertEqual(len(uploaded.json()["uploaded"]), 1)

            listing = client.get("/documents")
            self.assertEqual(listing.status_code, 200)
            self.assertEqual(listing.json()["documents"][0]["filename"], "facts.pdf")

            payload = {"question": "What is the capital of France?", "history": []}
            answer = client.post("/ask", json=payload)
            self.assertEqual(answer.status_code, 200)
            self.assertIn("Paris", answer.json()["answer"])
            self.assertTrue(answer.json()["sources"])

            stream = client.post("/ask/stream", json=payload)
            self.assertEqual(stream.status_code, 200)
            self.assertIn('"type": "sources"', stream.text)
            self.assertIn('"type": "done"', stream.text)


if __name__ == "__main__":
    unittest.main()
