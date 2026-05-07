import json

import pytest

import controller.ExerciseController as exercise_controller
from entity.Exercise import Exercise, ExerciseType
from entity.ExerciseSet import ExerciseSet
from service.ExerciseService import get_exercises_by_document_names
from tests.conftest import create_course, create_exercise, create_exercise_set, create_user


def test_upload_exercise_set_success(client, db_session, course_1):
    payload = {
        "course_id": course_1.id,
        "title": "高数练习一",
        "description": "覆盖三类题型",
        "document_id": "doc-001",
        "document_name": "doc-A.pdf",
        "questions": [
            {
                "type": "single",
                "question": "2 + 2 = ?",
                "options": ["1", "2", "3", "4"],
                "answer": "D",
            },
            {
                "type": "multiple",
                "question": "哪些是偶数？",
                "options": ["1", "2", "3", "4"],
                "answer": ["B", "D"],
            },
            {
                "type": "blank",
                "question": "软件测试英文是什么？",
                "options": [],
                "answer": ["software testing"],
            },
        ],
    }

    response = client.post("/api/exercise/upload", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True

    exercise_sets = db_session.query(ExerciseSet).all()
    exercises = db_session.query(Exercise).all()
    assert len(exercise_sets) == 1
    assert len(exercises) == 3
    assert {exercise.exercise_set_id for exercise in exercises} == {exercise_sets[0].id}
    assert json.loads(exercises[0].options) == ["1", "2", "3", "4"]
    assert json.loads(exercises[1].answer) == ["B", "D"]


def test_upload_exercise_set_returns_500_when_service_raises(client, monkeypatch, course_1):
    def boom(db, dto):
        raise Exception("mock error")

    monkeypatch.setattr(exercise_controller, "create_exercise_set", boom)

    payload = {
        "course_id": course_1.id,
        "title": "异常习题集",
        "description": "触发异常",
        "questions": [
            {
                "type": "single",
                "question": "题目",
                "options": ["A", "B"],
                "answer": "A",
            }
        ],
    }

    response = client.post("/api/exercise/upload", json=payload)

    assert response.status_code == 500
    assert response.json()["message"] == "mock error"


def test_search_exercise_sets_without_keyword(client, db_session, course_1):
    create_exercise_set(db_session, course_1, title="练习一")
    create_exercise_set(db_session, course_1, title="练习二")

    other_teacher = create_user(db_session, "other_teacher", "teacher")
    other_course = create_course(db_session, other_teacher, name="Other Course")
    create_exercise_set(db_session, other_course, title="其他课程练习")

    response = client.get(
        "/api/exercise/search",
        params={"course_id": course_1.id, "page": 1, "page_size": 1},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["total"] == 2
    assert len(body["data"]["items"]) == 1
    assert body["data"]["items"][0]["course_id"] == course_1.id


def test_search_exercise_sets_with_keyword_filter(client, db_session, course_1):
    create_exercise_set(db_session, course_1, title="线性代数练习")
    create_exercise_set(db_session, course_1, title="高等数学练习")

    response = client.get(
        "/api/exercise/search",
        params={
            "course_id": course_1.id,
            "keyword": "线性代数",
            "page": 1,
            "page_size": 10,
        },
    )

    assert response.status_code == 200
    items = response.json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["title"] == "线性代数练习"


def test_get_exercise_set_detail_success(client, exercise_set_1, exercise_bundle):
    response = client.get(f"/api/exercise/{exercise_set_1.id}")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["id"] == exercise_set_1.id
    assert len(body["data"]["exercises"]) == 3


def test_get_exercise_set_detail_not_found(client):
    response = client.get("/api/exercise/999999")

    assert response.status_code == 404
    assert response.json()["message"] == "ExerciseSet not found"


def test_delete_exercise_set_success(client, db_session, exercise_set_1, exercise_bundle):
    response = client.delete(f"/api/exercise/{exercise_set_1.id}")

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert db_session.query(ExerciseSet).filter(ExerciseSet.id == exercise_set_1.id).first() is None


def test_delete_exercise_set_not_found(client):
    response = client.delete("/api/exercise/999999")

    assert response.status_code == 404
    assert "未找到对应的习题集" in response.json()["message"]


def test_update_exercise_rejects_student(client, login_as, student_user, exercise_bundle):
    login_as(student_user)

    response = client.put(
        f"/api/exercise/{exercise_bundle['single'].id}",
        json={"question": "更新后的题目", "answer": "B"},
    )

    assert response.status_code == 403
    assert response.json()["message"] == "Only teachers can update exercises"


def test_update_exercise_success_for_teacher(client, login_as, teacher_user, db_session, exercise_bundle):
    login_as(teacher_user)
    exercise_id = exercise_bundle["single"].id

    response = client.put(
        f"/api/exercise/{exercise_id}",
        json={"question": "更新后的题目", "answer": "B"},
    )

    assert response.status_code == 200
    assert response.json()["success"] is True

    db_session.expire_all()
    updated = db_session.query(Exercise).filter(Exercise.id == exercise_id).first()
    assert updated.question == "更新后的题目"
    assert updated.answer == "B"


def test_update_exercise_returns_500_when_target_missing(client, login_as, teacher_user):
    login_as(teacher_user)

    response = client.put(
        "/api/exercise/999999",
        json={"question": "不存在的题目", "answer": "A"},
    )

    assert response.status_code == 500
    assert "习题不存在" in response.json()["message"]


def test_get_exercises_by_document_names_returns_deserialized_results(
    db_session, course_1
):
    set_a = create_exercise_set(db_session, course_1, title="A", document_name="doc-A.pdf")
    set_b = create_exercise_set(db_session, course_1, title="B", document_name="doc-B.pdf")
    create_exercise(
        db_session,
        set_a,
        "A题目",
        ExerciseType.single,
        ["A", "B"],
        "A",
    )
    create_exercise(
        db_session,
        set_b,
        "B题目",
        ExerciseType.multiple,
        ["A", "B"],
        ["A"],
    )

    results = get_exercises_by_document_names(db_session, ["doc-A.pdf"])

    assert len(results) == 1
    assert results[0]["question"] == "A题目"
    assert results[0]["options"] == ["A", "B"]
    assert results[0]["answer"] == "A"


def test_upload_empty_question_list_should_be_rejected(client, course_1):
    payload = {
        "course_id": course_1.id,
        "title": "空题目集",
        "description": "应被拒绝",
        "questions": [],
    }

    response = client.post("/api/exercise/upload", json=payload)

    assert response.status_code in {400, 422}
