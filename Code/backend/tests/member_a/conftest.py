from __future__ import annotations

from io import BytesIO
from pathlib import Path
import sys
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from config.db import Base, get_db
import controller.CourseController as CourseController
import controller.LoginController as LoginController
import entity.Comment  # noqa: F401
import entity.Course  # noqa: F401
import entity.Exercise  # noqa: F401
import entity.ExerciseSet  # noqa: F401
import entity.Post  # noqa: F401
import entity.User  # noqa: F401
import entity.UserAuth  # noqa: F401
import main
from entity.Course import Course
from entity.User import User
from entity.UserAuth import UserAuth
from service.LoginService import pwd_context


class FakeStream(BytesIO):
    def __init__(self, content: bytes, filename: str) -> None:
        super().__init__(content)
        self.filename = filename


class FakeDocumentDAO:
    def __init__(self) -> None:
        self.files = {
            "pdf-1": {
                "file_id": "pdf-1",
                "filename": "lesson.pdf",
                "course": "Software Testing",
                "size": 128,
                "upload_time": "2026-04-19 10:00:00",
                "content": b"%PDF-1.4 mock pdf",
            },
            "doc-1": {
                "file_id": "doc-1",
                "filename": "notes.txt",
                "course": "Software Testing",
                "size": 64,
                "upload_time": "2026-04-19 10:10:00",
                "content": b"plain text",
            },
        }

    def save_file(self, file_content: bytes, filename: str, course_name: str) -> str:
        file_id = f"file-{len(self.files) + 1}"
        self.files[file_id] = {
            "file_id": file_id,
            "filename": filename,
            "course": course_name,
            "size": len(file_content),
            "upload_time": "2026-04-19 11:00:00",
            "content": file_content,
        }
        return file_id

    def get_documents_by_course(self, course_name: str, page: int, size: int):
        matched = [item for item in self.files.values() if item["course"] == course_name]
        start = (page - 1) * size
        end = start + size
        return matched[start:end], len(matched)

    def get_file_stream(self, file_id: str):
        file = self.files.get(file_id)
        if not file:
            raise FileNotFoundError(file_id)
        return FakeStream(file["content"], file["filename"])

    def delete_file(self, file_id: str) -> bool:
        return self.files.pop(file_id, None) is not None


def seed_initial_data(session) -> None:
    teacher = User(
        username="teacher1",
        role="teacher",
        email="teacher1@example.com",
        name="Teacher One",
    )
    student = User(
        username="student1",
        role="student",
        email="student1@example.com",
        name="Student One",
    )
    session.add_all([teacher, student])
    session.flush()

    session.add_all(
        [
            UserAuth(user_id=teacher.id, hashed_password=pwd_context.hash("Pass123!")),
            UserAuth(user_id=student.id, hashed_password=pwd_context.hash("Pass123!")),
        ]
    )

    course = Course(
        name="Software Testing",
        description="default course",
        teacher_id=teacher.id,
        teacher=teacher,
    )
    student.joined_courses.append(course)
    session.add(course)
    session.commit()


@pytest.fixture
def session_factory():
    temp_root = Path(__file__).resolve().parent / "_runtime"
    temp_root.mkdir(exist_ok=True)
    db_path = temp_root / f"blackbox_test_{uuid.uuid4().hex}.db"
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    try:
        seed_initial_data(session)
    finally:
        session.close()

    yield TestingSessionLocal
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def client(session_factory):
    app = main.app
    fake_dao = FakeDocumentDAO()

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[LoginController.get_db] = override_get_db
    app.dependency_overrides[CourseController.get_db] = override_get_db
    main.rag_controller.document_dao = fake_dao

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def db_session(session_factory):
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def teacher_headers(client):
    response = client.post(
        "/api/login",
        json={"username": "teacher1", "password": "Pass123!"},
    )
    token = response.json()["data"]["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def student_headers(client):
    response = client.post(
        "/api/login",
        json={"username": "student1", "password": "Pass123!"},
    )
    token = response.json()["data"]["token"]
    return {"Authorization": f"Bearer {token}"}
