import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from fastapi import FastAPI

from controller.CourseController import router
from service.UserService import get_current_user

app = FastAPI()
app.include_router(router, prefix="/course")

class FakeUser:
    def __init__(self, role="teacher", id=1, username="user", email="u@x.com", name="user"):
        self.id = id
        self.role = role
        self.username = username
        self.email = email
        self.name = name
        self.courses = []
        self.joined_courses = []

    def __eq__(self, other):
        return isinstance(other, FakeUser) and self.id == other.id

class FakeCourse:
    def __init__(self, id=1, name="测试课程", description="描述", teacher_id=1, is_deleted=False, students=None, teacher=None):
        self.id = id
        self.name = name
        self.description = description
        self.teacher_id = teacher_id
        self.is_deleted = is_deleted
        self.students = students if students is not None else []
        self.teacher = teacher if teacher is not None else FakeUser(role="teacher", id=teacher_id, username="teacher", email="t@t.com", name="teacher")

    def __eq__(self, other):
        return isinstance(other, FakeCourse) and self.id == other.id

@pytest.fixture
def client():
    # 默认 teacher
    app.dependency_overrides[get_current_user] = lambda: FakeUser()
    yield TestClient(app)
    app.dependency_overrides = {}

# 1. /all 正常
@patch("controller.CourseController.fetch_all_courses", return_value=([FakeCourse()], 1))
def test_get_all_courses(mock_fetch, client):
    res = client.get("/course/all?page=1&page_size=1&keyword=")
    assert res.status_code == 200
    assert res.json()["success"] is True
    mock_fetch.assert_called_once()

# 2. /all include_dissolved True
@patch("controller.CourseController.fetch_all_courses", return_value=([FakeCourse()], 1))
def test_get_all_courses_include_dissolved(mock_fetch, client):
    res = client.get("/course/all?page=1&page_size=1&keyword=&include_dissolved=true")
    assert res.status_code == 200
    assert res.json()["success"] is True
    mock_fetch.assert_called_once()

# 3. /{course_id} 正常
@patch("controller.CourseController.fetch_course_by_id", return_value=FakeCourse())
def test_get_course_by_id(mock_fetch, client):
    res = client.get("/course/1")
    assert res.status_code == 200
    assert res.json()["data"]["name"] == "测试课程"

# 4. /{course_id} 不存在
@patch("controller.CourseController.fetch_course_by_id", return_value=None)
def test_get_course_by_id_not_found(mock_fetch, client):
    res = client.get("/course/999")
    assert res.status_code == 404
    assert res.json()["detail"] == "Course not found"

# 5. /create teacher
@patch("controller.CourseController.create_course", return_value=FakeCourse())
def test_create_course_teacher(mock_create, client):
    res = client.post("/course/create", json={"name": "新课程", "description": "desc"})
    assert res.status_code == 200
    assert res.json()["success"] is True
    assert res.json()["data"]["name"] == "测试课程"

# 6. /create 非 teacher
@patch("controller.CourseController.create_course")
def test_create_course_not_teacher(mock_create,client):
    app.dependency_overrides[get_current_user] = lambda: FakeUser(role="student")
    res = client.post("/course/create", json={"name": "新课程", "description": "desc"})
    assert res.status_code == 200
    assert res.json()["success"] is False
    assert res.json()["message"] == "Only teachers can create courses"
    app.dependency_overrides = {}

# 7. /teach 正常
@patch("controller.CourseController.fetch_teached_courses", return_value=([FakeCourse()], 1))
def test_get_taught_courses_teacher(mock_teach, client):
    res = client.get("/course/teach?page=1&page_size=1&keyword=")
    assert res.status_code == 200
    assert res.json()["data"]["total"] == 1

# 8. /teach 非 teacher
def test_get_taught_courses_student(client):
    app.dependency_overrides[get_current_user] = lambda: FakeUser(role="student")
    res = client.get("/course/teach?page=1&page_size=1&keyword=")
    assert res.status_code == 200
    assert res.json()["success"] is False
    assert res.json()["message"] == "Only teachers can view their taught courses"
    app.dependency_overrides = {}

# 9. /teach 非老师分支
@patch("controller.CourseController.fetch_teached_courses", return_value=([FakeCourse()], 1))
def test_get_taught_courses_not_teacher(mock_teach, client):
    app.dependency_overrides[get_current_user] = lambda: FakeUser(role="student")
    res = client.get("/course/teach?page=1&page_size=1&keyword=")
    assert res.status_code == 200
    assert res.json()["success"] is False
    assert res.json()["message"] == "Only teachers can view their taught courses"
    app.dependency_overrides = {}

# 10. /join 正常
@patch("controller.CourseController.join_course", return_value=FakeCourse())
def test_join_course(mock_join, client):
    app.dependency_overrides[get_current_user] = lambda: FakeUser(role="student")
    res = client.post("/course/join/1")
    assert res.status_code == 200
    assert res.json()["success"] is True

# 11. /join 失败
@patch("controller.CourseController.join_course", return_value=None)
def test_join_course_fail(mock_join, client):
    app.dependency_overrides[get_current_user] = lambda: FakeUser(role="student")
    res = client.post("/course/join/1")
    assert res.status_code == 200
    assert res.json()["success"] is False
    assert res.json()["message"] == "Join course failed"

# 12. /quit 正常
@patch("controller.CourseController.quit_course", return_value=FakeCourse())
def test_quit_course(mock_quit, client):
    app.dependency_overrides[get_current_user] = lambda: FakeUser(role="student")
    res = client.post("/course/quit/1")
    assert res.status_code == 200
    assert res.json()["success"] is True

# 13. /quit 失败
@patch("controller.CourseController.quit_course", return_value=None)
def test_quit_course_fail(mock_quit, client):
    app.dependency_overrides[get_current_user] = lambda: FakeUser(role="student")
    res = client.post("/course/quit/1")
    assert res.status_code == 200
    assert res.json()["success"] is False
    assert res.json()["message"] == "Quit course failed"

# 14. /join/{course_id} 正常
@patch("controller.CourseController.join_course", return_value=FakeCourse())
def test_join_course_endpoint(mock_join, client):
    app.dependency_overrides[get_current_user] = lambda: FakeUser(role="student")
    res = client.post("/course/join/1")
    assert res.status_code == 200
    assert res.json()["success"] is True
    app.dependency_overrides = {}

# 15. /quit/{course_id} 正常
@patch("controller.CourseController.quit_course", return_value=FakeCourse())
def test_quit_course_endpoint(mock_quit, client):
    app.dependency_overrides[get_current_user] = lambda: FakeUser(role="student")
    res = client.post("/course/quit/1")
    assert res.status_code == 200
    assert res.json()["success"] is True
    app.dependency_overrides = {}

# 16. /join/{course_id} 非学生
@patch("controller.CourseController.join_course", return_value=FakeCourse())
def test_join_course_endpoint_not_student(mock_join, client):
    app.dependency_overrides[get_current_user] = lambda: FakeUser(role="teacher")
    res = client.post("/course/join/1")
    assert res.status_code == 200
    assert res.json()["success"] is False
    assert res.json()["message"] == "Only students can join courses"
    app.dependency_overrides = {}

# 17. /quit/{course_id} 非学生
@patch("controller.CourseController.quit_course", return_value=FakeCourse())
def test_quit_course_endpoint_not_student(mock_quit, client):
    app.dependency_overrides[get_current_user] = lambda: FakeUser(role="teacher")
    res = client.post("/course/quit/1")
    assert res.status_code == 200
    assert res.json()["success"] is False
    assert res.json()["message"] == "Only students can quit courses"
    app.dependency_overrides = {}

# 18. /create 非老师
@patch("controller.CourseController.create_course", return_value=FakeCourse())
def test_create_course_endpoint_not_teacher(mock_create, client):
    app.dependency_overrides[get_current_user] = lambda: FakeUser(role="student")
    res = client.post("/course/create", json={"name": "新课程", "description": "desc"})
    assert res.status_code == 200
    assert res.json()["success"] is False
    assert res.json()["message"] == "Only teachers can create courses"
    app.dependency_overrides = {}

# 19. /dissolve/{course_id} 非老师
@patch("controller.CourseController.dissolve_course_by_id", return_value=FakeCourse())
def test_dissolve_course_endpoint_not_teacher(mock_dissolve, client):
    app.dependency_overrides[get_current_user] = lambda: FakeUser(role="student")
    res = client.post("/course/dissolve/1")
    assert res.status_code == 200
    assert res.json()["success"] is False
    assert res.json()["message"] == "Only teachers can dissolve courses"
    app.dependency_overrides = {}

# /course/join 正常分支
@patch("controller.CourseController.fetch_joined_courses", return_value=([FakeCourse()], 1))
def test_get_joined_courses_normal(mock_fetch, client):
    res = client.get("/course/join?page=1&page_size=1&keyword=")
    assert res.status_code == 200
    assert res.json()["success"] is True
    assert res.json()["data"]["courses"][0]["name"] == "测试课程"

# /dissolve/{course_id} 正常分支
@patch("controller.CourseController.dissolve_course_by_id", return_value=FakeCourse())
def test_dissolve_course_success(mock_dissolve, client):
    app.dependency_overrides[get_current_user] = lambda: FakeUser(role="teacher")
    res = client.post("/course/dissolve/1")
    assert res.status_code == 200
    assert res.json()["success"] is True
    assert res.json()["data"]["name"] == "测试课程"
    app.dependency_overrides = {}

@patch("controller.CourseController.fetch_joined_courses", return_value=([], 0))
def test_get_joined_courses_empty(mock_fetch, client):
    res = client.get("/course/join?page=1&page_size=1&keyword=")
    assert res.status_code == 200
    assert res.json()["success"] is False
    assert res.json()["message"] == "No joined courses found"
    assert res.json()["data"]["courses"] == []
    assert res.json()["data"]["total"] == 0

@patch("controller.CourseController.dissolve_course_by_id", return_value=None)
def test_dissolve_course_fail(mock_dissolve, client):
    app.dependency_overrides[get_current_user] = lambda: FakeUser(role="teacher")
    res = client.post("/course/dissolve/1")
    assert res.status_code == 200
    assert res.json()["success"] is False
    assert res.json()["message"] == "Dissolve course failed"
    app.dependency_overrides = {}

@patch("controller.CourseController.fetch_teached_courses", return_value=([], 0))
def test_get_taught_courses_empty_for_teacher(mock_fetch, client):
    app.dependency_overrides[get_current_user] = lambda: FakeUser(role="teacher")
    res = client.get("/course/teach?page=1&page_size=1&keyword=")
    assert res.status_code == 200
    assert res.json()["success"] is False
    assert res.json()["message"] == "No taught courses found"
    assert res.json()["data"]["courses"] == []
    assert res.json()["data"]["total"] == 0
    app.dependency_overrides = {}