import io
import zipfile

from fastapi import FastAPI
from fastapi.testclient import TestClient

import controller.rag_controller as rag_controller
from dao.document_dao import DocumentDAO
import repository.document_repository as document_repository_module
from repository.document_repository import DocumentRepository


class _NamedBytesIO(io.BytesIO):
    def __init__(self, data: bytes, filename: str):
        super().__init__(data)
        self.filename = filename


def _install_fake_document_backend(monkeypatch):
    store = {}

    class _Cursor:
        def __init__(self, items):
            self._items = items

        def skip(self, _n):
            return self

        def limit(self, _n):
            return self

        def sort(self, *_args, **_kwargs):
            return self

        def __iter__(self):
            return iter(self._items)

    class _FilesCollection:
        def count_documents(self, query):
            course = query.get("metadata.course")
            return len([v for v in store.values() if v["metadata"].get("course") == course])

        def find(self, query):
            course = query.get("metadata.course")
            items = [v for v in store.values() if v["metadata"].get("course") == course]
            return _Cursor(items)

    class _FakeGridOut(_NamedBytesIO):
        def __init__(self, file_id, row):
            super().__init__(row["content"], row["filename"])
            self._id = file_id
            self.metadata = row["metadata"]
            self.length = len(row["content"])
            self.upload_date = None

    class _FakeFS:
        def put(self, content, filename=None, metadata=None):
            file_id = f"id-{len(store) + 1}"
            store[file_id] = {
                "_id": file_id,
                "filename": filename,
                "metadata": metadata or {},
                "content": content,
                "length": len(content),
            }
            return file_id

        def get(self, file_id):
            if file_id not in store:
                raise FileNotFoundError
            return _FakeGridOut(file_id, store[file_id])

        def delete(self, file_id):
            if file_id not in store:
                raise Exception("not found")
            del store[file_id]

        def find(self):
            return [_FakeGridOut(file_id, row) for file_id, row in store.items()]

    class _FakeClient:
        def __init__(self):
            self.db = type("DB", (), {"fs": type("FS", (), {"files": _FilesCollection()})()})()

        def __getitem__(self, _name):
            return self.db

    monkeypatch.setattr(document_repository_module, "MongoClient", lambda uri: _FakeClient())
    monkeypatch.setattr(document_repository_module.gridfs, "GridFS", lambda db: _FakeFS())
    monkeypatch.setattr(document_repository_module, "ObjectId", lambda x: x)

    return DocumentDAO(DocumentRepository())


def _build_client(monkeypatch):
    app = FastAPI()
    app.include_router(rag_controller.router)
    rag_controller.document_dao = _install_fake_document_backend(monkeypatch)
    return TestClient(app)


def test_rag_flow_upload_list_download_preview_delete(monkeypatch):
    client = _build_client(monkeypatch)

    upload_resp = client.post(
        "/api/rag/add_document_batch",
        data={"course_name": "course1"},
        files=[("files", ("demo.pdf", b"%PDF-1.4 fake", "application/pdf"))],
    )
    assert upload_resp.status_code == 200
    assert upload_resp.json()["message"] == "Documents added successfully."
    file_id = upload_resp.json()["file_ids"][0]

    list_resp = client.get("/api/rag/documents?course_name=course1&page=1&size=10")
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] == 1

    download_resp = client.get(f"/api/rag/download/{file_id}")
    assert download_resp.status_code == 200
    assert "attachment;" in download_resp.headers["content-disposition"]

    preview_resp = client.get(f"/api/rag/preview/{file_id}")
    assert preview_resp.status_code == 200
    assert "inline;" in preview_resp.headers["content-disposition"]

    delete_resp = client.delete(f"/api/rag/delete_document/{file_id}")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["success"] is True


def test_rag_flow_zip_nested_rejected(monkeypatch):
    client = _build_client(monkeypatch)

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        zip_file.writestr("nested/dir/a.txt", b"content")
    zip_buffer.seek(0)

    resp = client.post(
        "/api/rag/add_document_batch",
        data={"course_name": "course1"},
        files=[("files", ("nested.zip", zip_buffer.getvalue(), "application/zip"))],
    )
    assert resp.status_code == 400
    assert "暂不支持嵌套文件夹上传" in resp.json()["detail"]


def test_rag_flow_error_branches(monkeypatch):
    client = _build_client(monkeypatch)

    upload_txt = client.post(
        "/api/rag/add_document_batch",
        data={"course_name": "course1"},
        files=[("files", ("note.txt", b"abc", "text/plain"))],
    )
    txt_id = upload_txt.json()["file_ids"][0]

    non_pdf_resp = client.get(f"/api/rag/preview/{txt_id}")
    assert non_pdf_resp.status_code == 400
    assert non_pdf_resp.json()["detail"] == "仅支持 PDF 文件预览"

    missing_download = client.get("/api/rag/download/not-exist")
    assert missing_download.status_code == 404

    missing_preview = client.get("/api/rag/preview/not-exist")
    assert missing_preview.status_code == 404

    missing_delete = client.delete("/api/rag/delete_document/not-exist")
    assert missing_delete.status_code == 404

    monkeypatch.setattr(rag_controller.settings, "MAX_FILE_SIZE", 2)
    too_large_resp = client.post(
        "/api/rag/add_document_batch",
        data={"course_name": "course1"},
        files=[("files", ("big.txt", b"abcd", "text/plain"))],
    )
    assert too_large_resp.status_code == 413

    multimodal = client.post(
        "/api/rag/add_document_multimodal_batch",
        data={"course_name": "course1"},
        files=[("files", ("m.txt", b"a", "text/plain"))],
    )
    assert multimodal.status_code == 200


def test_rag_flow_zip_and_total_size_paths(monkeypatch):
    client = _build_client(monkeypatch)

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        zip_file.writestr("folder/", b"")
        zip_file.writestr("folder/a.txt", b"1")
        zip_file.writestr("b.txt", b"2")
    zip_buffer.seek(0)
    ok_zip = client.post(
        "/api/rag/add_document_batch",
        data={"course_name": "course1"},
        files=[("files", ("ok.zip", zip_buffer.getvalue(), "application/zip"))],
    )
    assert ok_zip.status_code == 200
    assert len(ok_zip.json()["file_ids"]) == 2

    monkeypatch.setattr(rag_controller.settings, "MAX_FILE_SIZE", 3)
    total_too_large = client.post(
        "/api/rag/add_document_batch",
        data={"course_name": "course1"},
        files=[
            ("files", ("a.txt", b"ab", "text/plain")),
            ("files", ("b.txt", b"cd", "text/plain")),
        ],
    )
    assert total_too_large.status_code == 413

    monkeypatch.setattr(rag_controller.settings, "MAX_FILE_SIZE", 50000)
    zip_big = io.BytesIO()
    with zipfile.ZipFile(zip_big, "w", compression=zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("a.txt", b"a" * 300000)
    zip_big.seek(0)
    unzip_too_large = client.post(
        "/api/rag/add_document_batch",
        data={"course_name": "course1"},
        files=[("files", ("big.zip", zip_big.getvalue(), "application/zip"))],
    )
    assert unzip_too_large.status_code == 413
    assert "解压后的文件总大小超过限制" in unzip_too_large.json()["detail"]


def test_rag_flow_dao_not_initialized_path(monkeypatch):
    app = FastAPI()
    app.include_router(rag_controller.router)
    rag_controller.document_dao = None
    client = TestClient(app)
    resp = client.get("/api/rag/documents?course_name=course1&page=1&size=10")
    assert resp.status_code == 500

