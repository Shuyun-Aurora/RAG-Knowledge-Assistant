from entity.Course import Course
from entity.ExerciseSet import ExerciseSet
from entity.Post import Post


def test_core_flow_teacher_builds_course_and_student_joins_then_interacts(
    client,
    teacher_headers,
    student_headers,
    db_session,
):
    create_course_response = client.post(
        "/api/course/create",
        json={"name": "Integrated Testing Course", "description": "full black-box flow"},
        headers=teacher_headers,
    )
    assert create_course_response.status_code == 200
    assert create_course_response.json()["success"] is True
    course_id = create_course_response.json()["data"]["id"]

    upload_doc_response = client.post(
        "/api/rag/add_document_batch",
        data={"course_name": "Integrated Testing Course"},
        files={"files": ("flow.pdf", b"%PDF-1.4 integrated", "application/pdf")},
    )
    assert upload_doc_response.status_code == 200
    assert len(upload_doc_response.json()["file_ids"]) == 1

    upload_exercise_response = client.post(
        "/api/exercise/upload",
        json={
            "course_id": course_id,
            "title": "Integrated Quiz",
            "description": "integration flow",
            "questions": [
                {"type": "single", "question": "1+1=?", "options": ["1", "2"], "answer": "B"}
            ],
        },
        headers=teacher_headers,
    )
    assert upload_exercise_response.status_code == 200
    assert upload_exercise_response.json()["success"] is True

    join_response = client.post(f"/api/course/join/{course_id}", headers=student_headers)
    assert join_response.status_code == 200
    assert join_response.json()["success"] is True

    docs_response = client.get("/api/rag/documents?course_name=Integrated%20Testing%20Course&page=1&size=10")
    assert docs_response.status_code == 200
    assert docs_response.json()["total"] >= 1

    exercise_set = db_session.query(ExerciseSet).filter(ExerciseSet.title == "Integrated Quiz").first()
    assert exercise_set is not None
    exercise_detail_response = client.get(f"/api/exercise/{exercise_set.id}", headers=student_headers)
    assert exercise_detail_response.status_code == 200
    assert exercise_detail_response.json()["data"]["title"] == "Integrated Quiz"

    post_response = client.post(
        f"/api/course/{course_id}/post/create",
        json={"title": "Question", "content": "I joined the course", "is_anonymous": False},
        headers=student_headers,
    )
    assert post_response.status_code == 200
    post_body = post_response.json()
    assert post_body["success"] is True
    assert post_body["data"]["author"] == "student1"

    created_post = db_session.query(Post).filter(Post.title == "Question").first()
    assert created_post is not None
    comment_response = client.post(
        f"/api/course/posts/{created_post.id}/comments",
        json={"content": "This is helpful.", "parent_id": None, "is_anonymous": False},
        headers=teacher_headers,
    )
    assert comment_response.status_code == 200
    assert comment_response.json()["success"] is True

    created_course = db_session.query(Course).filter(Course.id == course_id).first()
    assert created_course is not None
    assert any(student.username == "student1" for student in created_course.students)
