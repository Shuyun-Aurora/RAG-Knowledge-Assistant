import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from fastapi import FastAPI
from datetime import datetime

from controller.ExerciseController import router
from service.UserService import get_current_user

app = FastAPI()
app.include_router(router, prefix="")

@pytest.fixture
def client():
    app.dependency_overrides[get_current_user] = lambda: type("User", (), {"role": "teacher", "id": 1})()
    yield TestClient(app)
    app.dependency_overrides = {}

@patch("controller.ExerciseController.create_exercise_set")
def test_upload_exercise_set_success(mock_create, client):
    data = {
        "course_id": 1,
        "title": "测试集",
        "description": "描述",
        "document_id": "1",
        "document_name": "doc.pdf",
        "questions": [
            {
                "question": "Q1",
                "type": "single",
                "options": ["A", "B"],
                "answer": "A"
            }
        ]
    }
    res = client.post("/api/exercise/upload", json=data)
    assert res.status_code == 200
    assert res.json()["success"] is True
    assert res.json()["message"] == "Exercise set created"

# 2. 上传习题集失败
@patch("controller.ExerciseController.create_exercise_set", side_effect=Exception("fail"))
def test_upload_exercise_set_fail(mock_create, client):
    data = {
        "course_id": 1,
        "title": "测试集",
        "description": "描述",
        "document_id": "1",
        "document_name": "doc.pdf",
        "questions": []
    }
    res = client.post("/api/exercise/upload", json=data)
    assert res.status_code == 500
    assert res.json()["detail"] == "fail"

# 3. 查询习题集分页
@patch("controller.ExerciseController.search_exercise_sets_service")
def test_search_exercise_sets(mock_search, client):
    class FakePage:
        total = 1
        items = [
            {
                "id": 1,
                "course_id": 1,
                "title": "测试集",
                "description": "描述",
                "created_at": datetime.now(),
                "document_id": "1",
                "document_name": "doc.pdf",
                "exercises": []
            }
        ]
    mock_search.return_value = FakePage()
    res = client.get("/api/exercise/search?course_id=1&page=1&page_size=10")
    assert res.status_code == 200
    assert res.json()["success"] is True
    assert res.json()["message"] == "查询成功"

# # 4. 查询习题集详情成功
@patch("controller.ExerciseController.get_exercise_set_detail_service", return_value={
    "id": 1,
    "course_id": 1,
    "title": "测试集",
    "description": "描述",
    "created_at": datetime.now(),
    "document_id": "1",
    "document_name": "doc.pdf",
    "exercises": []
})
def test_get_exercise_set_detail_success(mock_detail, client):
    res = client.get("/api/exercise/1")
    assert res.status_code == 200
    assert res.json()["success"] is True
    assert res.json()["message"] == "查询成功"

# # 5. 查询习题集详情失败
@patch("controller.ExerciseController.get_exercise_set_detail_service", side_effect=Exception("ExerciseSet not found"))
def test_get_exercise_set_detail_fail(mock_detail, client):
    res = client.get("/api/exercise/999")
    assert res.status_code == 404
    assert res.json()["detail"] == "ExerciseSet not found"

# # 6. 删除习题集成功
@patch("service.ExerciseService.delete_exercise_set_service")
def test_delete_exercise_set_success(mock_delete, client):
    mock_delete.return_value = None  # 返回 None，不检查返回值
    res = client.delete("/api/exercise/1")
    assert res.status_code == 200
    assert res.json()["success"] is True
    assert res.json()["message"] == "删除成功"

# 7. 删除习题集失败
@patch("service.ExerciseService.delete_exercise_set_service", side_effect=Exception("未找到对应的习题集"))
def test_delete_exercise_set_fail(mock_delete, client):
    res = client.delete("/api/exercise/1")
    assert res.status_code == 404
    assert res.json()["detail"] == "未找到对应的习题集"

# 8. 更新习题成功
@patch("controller.ExerciseController.update_exercise_service", return_value=None)
def test_update_exercise_success(mock_update, client):
    data = {
        "question": "新题目",
        "answer": "A"
    }
    res = client.put("/api/exercise/1", json=data)
    assert res.status_code == 200
    assert res.json()["success"] is True
    assert res.json()["message"] == "Exercise updated successfully"

# 9. 更新习题失败
@patch("controller.ExerciseController.update_exercise_service", side_effect=Exception("fail"))
def test_update_exercise_fail(mock_update, client):
    data = {
        "question": "新题目",
        "answer": "A"
    }
    res = client.put("/api/exercise/1", json=data)
    assert res.status_code == 500
    assert res.json()["detail"] == "fail"

# 10. 非教师更新习题
def test_update_exercise_forbidden(client):
    app.dependency_overrides[get_current_user] = lambda: type("User", (), {"role": "student", "id": 1})()
    data = {
        "question": "新题目",
        "answer": "A"
    }
    res = client.put("/api/exercise/1", json=data)
    assert res.status_code == 403
    assert res.json()["detail"] == "Only teachers can update exercises"
    app.dependency_overrides = {}
