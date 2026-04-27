from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi import FastAPI
from fastapi.testclient import TestClient

import controller.CourseController as course_controller
import controller.LoginController as login_controller
import controller.UserController as user_controller
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
    reg = client.post("/api/register", json={"username": username, "password": password, "role": role})
    assert reg.status_code == 200
    assert reg.json()["success"] is True
    login = client.post("/api/login", json={"username": username, "password": password})
    assert login.status_code == 200
    return login.json()["data"]["token"]


def test_course_flow_teacher_and_student_happy_path():
    client = _build_client()
    teacher_token = _register_and_login(client, "teacher1", "pwd123", "teacher")
    student_token = _register_and_login(client, "student1", "pwd123", "student")

    teacher_headers = {"Authorization": f"Bearer {teacher_token}"}
    student_headers = {"Authorization": f"Bearer {student_token}"}

    create_resp = client.post(
        "/api/course/create",
        json={"name": "AI", "description": "intro"},
        headers=teacher_headers,
    )
    assert create_resp.status_code == 200
    assert create_resp.json()["success"] is True
    course_id = create_resp.json()["data"]["id"]

    join_resp = client.post(f"/api/course/join/{course_id}", headers=student_headers)
    assert join_resp.status_code == 200
    assert join_resp.json()["success"] is True

    quit_resp = client.post(f"/api/course/quit/{course_id}", headers=student_headers)
    assert quit_resp.status_code == 200
    assert quit_resp.json()["success"] is True

    dissolve_resp = client.post(f"/api/course/dissolve/{course_id}", headers=teacher_headers)
    assert dissolve_resp.status_code == 200
    assert dissolve_resp.json()["success"] is True
    assert dissolve_resp.json()["data"]["is_deleted"] is True

    detail = client.get(f"/api/course/{course_id}")
    assert detail.status_code == 200
    assert detail.json()["success"] is True


def test_course_flow_permission_and_error_paths():
    client = _build_client()
    teacher_token = _register_and_login(client, "teacher2", "pwd123", "teacher")
    student_token = _register_and_login(client, "student2", "pwd123", "student")
    teacher_headers = {"Authorization": f"Bearer {teacher_token}"}
    student_headers = {"Authorization": f"Bearer {student_token}"}

    create_by_student = client.post(
        "/api/course/create",
        json={"name": "X", "description": "Y"},
        headers=student_headers,
    )
    assert create_by_student.status_code == 200
    assert create_by_student.json()["success"] is False

    join_by_teacher = client.post("/api/course/join/9999", headers=teacher_headers)
    assert join_by_teacher.status_code == 200
    assert join_by_teacher.json()["success"] is False

    not_found = client.get("/api/course/9999", headers=student_headers)
    assert not_found.status_code == 404

    create_resp = client.post(
        "/api/course/create",
        json={"name": "Data", "description": "d"},
        headers=teacher_headers,
    )
    course_id = create_resp.json()["data"]["id"]

    duplicate_join_1 = client.post(f"/api/course/join/{course_id}", headers=student_headers)
    assert duplicate_join_1.status_code == 200
    assert duplicate_join_1.json()["success"] is True
    duplicate_join_2 = client.post(f"/api/course/join/{course_id}", headers=student_headers)
    assert duplicate_join_2.status_code == 400

    second_teacher_token = _register_and_login(client, "teacher3", "pwd123", "teacher")
    bad_dissolve = client.post(
        f"/api/course/dissolve/{course_id}",
        headers={"Authorization": f"Bearer {second_teacher_token}"},
    )
    assert bad_dissolve.status_code == 403

    student_dissolve = client.post(f"/api/course/dissolve/{course_id}", headers=student_headers)
    assert student_dissolve.status_code == 200
    assert student_dissolve.json()["success"] is False

    teacher_quit = client.post(f"/api/course/quit/{course_id}", headers=teacher_headers)
    assert teacher_quit.status_code == 200
    assert teacher_quit.json()["success"] is False

    _ = client.post(f"/api/course/dissolve/{course_id}", headers=teacher_headers)
    already_dissolved_join = client.post(f"/api/course/join/{course_id}", headers=student_headers)
    assert already_dissolved_join.status_code == 400

    student_join_missing = client.post("/api/course/join/123456", headers=student_headers)
    assert student_join_missing.status_code == 404

    student_quit_missing = client.post("/api/course/quit/123456", headers=student_headers)
    assert student_quit_missing.status_code == 404

    duplicate_name = client.post(
        "/api/course/create",
        json={"name": "Data", "description": "new"},
        headers=teacher_headers,
    )
    assert duplicate_name.status_code == 400

    dissolve_missing = client.post("/api/course/dissolve/123456", headers=teacher_headers)
    assert dissolve_missing.status_code == 404

    second_dissolve = client.post(f"/api/course/dissolve/{course_id}", headers=teacher_headers)
    assert second_dissolve.status_code == 400

    filtered_teacher_courses = client.get(
        "/api/course/teach?include_dissolved=false&keyword=Dat",
        headers=teacher_headers,
    )
    assert filtered_teacher_courses.status_code == 200
    assert filtered_teacher_courses.json()["success"] is True

    filtered_joined_courses = client.get(
        "/api/course/join?include_dissolved=false&keyword=Dat",
        headers=student_headers,
    )
    assert filtered_joined_courses.status_code == 200
    assert filtered_joined_courses.json()["success"] is True

