from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi import FastAPI
from fastapi.testclient import TestClient

import controller.LoginController as login_controller
import controller.UserController as user_controller
import controller.CourseController as course_controller
from config.db import Base
import entity.User  # noqa: F401
import entity.UserAuth  # noqa: F401
import entity.Course  # noqa: F401


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

    def _get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[login_controller.get_db] = _get_db
    app.dependency_overrides[user_controller.get_db] = _get_db
    app.dependency_overrides[course_controller.get_db] = _get_db
    return TestClient(app)


def _register_and_login(client: TestClient, username: str, password: str, role: str) -> str:
    assert client.post("/api/register", json={"username": username, "password": password, "role": role}).json()["success"] is True
    login = client.post("/api/login", json={"username": username, "password": password})
    return login.json()["data"]["token"]


def test_course_controller_list_paths():
    client = _build_client()
    teacher_token = _register_and_login(client, "teacher_path", "pwd123", "teacher")
    student_token = _register_and_login(client, "student_path", "pwd123", "student")
    teacher_headers = {"Authorization": f"Bearer {teacher_token}"}
    student_headers = {"Authorization": f"Bearer {student_token}"}

    create = client.post("/api/course/create", json={"name": "ML", "description": "d"}, headers=teacher_headers)
    assert create.status_code == 200

    all_courses = client.get("/api/course/all?page=1&page_size=12&keyword=M")
    assert all_courses.status_code == 200
    assert all_courses.json()["success"] is True

    teacher_courses = client.get("/api/course/teach", headers=teacher_headers)
    assert teacher_courses.status_code == 200
    assert teacher_courses.json()["success"] is True

    teacher_courses_forbidden = client.get("/api/course/teach", headers=student_headers)
    assert teacher_courses_forbidden.status_code == 200
    assert teacher_courses_forbidden.json()["success"] is False


def test_course_controller_joined_and_quit_fail_paths():
    client = _build_client()
    teacher_token = _register_and_login(client, "teacher_path2", "pwd123", "teacher")
    student_token = _register_and_login(client, "student_path2", "pwd123", "student")
    teacher_headers = {"Authorization": f"Bearer {teacher_token}"}
    student_headers = {"Authorization": f"Bearer {student_token}"}

    create = client.post("/api/course/create", json={"name": "DB", "description": "d"}, headers=teacher_headers)
    cid = create.json()["data"]["id"]

    not_joined_quit = client.post(f"/api/course/quit/{cid}", headers=student_headers)
    assert not_joined_quit.status_code == 400

    join = client.post(f"/api/course/join/{cid}", headers=student_headers)
    assert join.status_code == 200
    joined_list = client.get("/api/course/join", headers=student_headers)
    assert joined_list.status_code == 200
    assert joined_list.json()["success"] is True

