from io import BytesIO
from pathlib import Path
import zipfile

import controller.rag_controller as rag_controller


def test_upload_single_document_succeeds(client):
    response = client.post(
        "/api/rag/add_document_batch",
        data={"course_name": "Software Testing"},
        files={"files": ("lesson.pdf", b"%PDF-1.4 lesson", "application/pdf")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "Documents added successfully."
    assert len(body["file_ids"]) == 1


def test_upload_nested_zip_is_rejected(client, monkeypatch):
    temp_root = Path(__file__).resolve().parent / "_tmp_zip"
    temp_root.mkdir(exist_ok=True)

    class LocalTemporaryDirectory:
        def __init__(self):
            self.path = temp_root / "case_nested_zip"

        def __enter__(self):
            self.path.mkdir(exist_ok=True)
            return str(self.path)

        def __exit__(self, exc_type, exc, tb):
            for item in self.path.iterdir():
                item.unlink()
            self.path.rmdir()

    monkeypatch.setattr(rag_controller.tempfile, "TemporaryDirectory", LocalTemporaryDirectory)

    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w") as zip_file:
        zip_file.writestr("outer/inner/file.txt", "nested content")
    buffer.seek(0)

    response = client.post(
        "/api/rag/add_document_batch",
        data={"course_name": "Software Testing"},
        files={"files": ("materials.zip", buffer.read(), "application/zip")},
    )

    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False
    assert "嵌套文件夹" in body["message"]


def test_get_documents_by_course_returns_list(client):
    response = client.get("/api/rag/documents?course_name=Software%20Testing&page=1&size=10")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 1
    assert body["documents"][0]["course"] == "Software Testing"


def test_preview_pdf_returns_pdf_content(client):
    response = client.get("/api/rag/preview/pdf-1")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/pdf")
    assert response.content.startswith(b"%PDF")


def test_preview_non_pdf_is_rejected(client):
    response = client.get("/api/rag/preview/doc-1")

    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False
    assert "仅支持 PDF 文件预览" in body["message"]


def test_delete_document_succeeds(client):
    response = client.delete("/api/rag/delete_document/doc-1")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["file_id"] == "doc-1"


def test_download_document_returns_attachment(client):
    response = client.get("/api/rag/download/pdf-1")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/octet-stream")
    assert "attachment;" in response.headers["content-disposition"]
    assert "lesson.pdf" in response.headers["content-disposition"]
