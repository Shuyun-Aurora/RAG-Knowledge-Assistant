import io
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi import FastAPI
from fastapi.testclient import TestClient

import controller.LoginController as login_controller
import controller.UserController as user_controller
import controller.CourseController as course_controller
import controller.rag_controller as rag_controller
from config.db import Base
import entity.User  # noqa: F401
import entity.UserAuth  # noqa: F401
import entity.Course  # noqa: F401


class _NamedBytesIO(io.BytesIO):
    def __init__(self, data: bytes, filename: str):
        super().__init__(data)
        self.filename = filename


class _FakeDao:
    def __init__(self):
        self.last_file_id = None
        self.files = {"pdf-id": _NamedBytesIO(b"%PDF-1.4 x", "x.pdf")}

    def save_file(self, file_content, filename, course_name):
        return "pdf-id"

    def get_documents_by_course(self, course_name, page, size):
        return ([{"file_id": "pdf-id", "filename": "x.pdf", "course": course_name, "size": 12}], 1)

    def get_file_stream(self, file_id):
        self.last_file_id = file_id
        if file_id not in self.files:
            raise FileNotFoundError
        return _NamedBytesIO(self.files[file_id].getvalue(), self.files[file_id].filename)

    def delete_file(self, file_id):
        return True


def _build_client() -> TestClient:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    app = FastAPI()
    app.include_router(login_controller.router, prefix="/api")
    app.include_router(user_controller.router, prefix="/api/user")
    app.include_router(course_controller.router, prefix="/api/course")
    app.include_router(rag_controller.router)

    def _get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[login_controller.get_db] = _get_db
    app.dependency_overrides[user_controller.get_db] = _get_db
    app.dependency_overrides[course_controller.get_db] = _get_db
    rag_controller.document_dao = _FakeDao()
    return TestClient(app)


def _register_and_login(client: TestClient, username: str, password: str, role: str) -> str:
    assert client.post("/api/register", json={"username": username, "password": password, "role": role}).json()["success"] is True
    return client.post("/api/login", json={"username": username, "password": password}).json()["data"]["token"]


def test_du_user_id_role_and_course_id_via_controller():
    client = _build_client()
    teacher_token = _register_and_login(client, "teacher_du", "pwd123", "teacher")
    student_token = _register_and_login(client, "student_du", "pwd123", "student")
    teacher_headers = {"Authorization": f"Bearer {teacher_token}"}
    student_headers = {"Authorization": f"Bearer {student_token}"}

    # role=teacher 才可创建课程；course_id 在后续 join/quit 路径中被持续使用
    created = client.post("/api/course/create", json={"name": "DU", "description": "d"}, headers=teacher_headers)
    cid = created.json()["data"]["id"]
    assert client.post(f"/api/course/join/{cid}", headers=student_headers).status_code == 200
    assert client.post(f"/api/course/quit/{cid}", headers=student_headers).status_code == 200


def test_du_file_id_via_controller_path():
    client = _build_client()
    dao = rag_controller.document_dao

    upload = client.post(
        "/api/rag/add_document_batch",
        data={"course_name": "c1"},
        files=[("files", ("a.txt", b"abc", "text/plain"))],
    )
    assert upload.status_code == 200

    download = client.get("/api/rag/download/pdf-id")
    assert download.status_code == 200
    assert dao.last_file_id == "pdf-id"

    missing = client.get("/api/rag/download/not-exist")
    assert missing.status_code == 404

