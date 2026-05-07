from entity.Course import Course
from entity.ExerciseSet import ExerciseSet
from entity.Post import Post


def test_upload_exercise_set_succeeds(client, teacher_headers, db_session):
    course = db_session.query(Course).filter(Course.name == "Software Testing").first()
    assert course is not None

    payload = {
        "course_id": course.id,
        "title": "Chapter 1 Quiz",
        "description": "basic questions",
        "questions": [
            {"type": "single", "question": "2+2=?", "options": ["3", "4", "5"], "answer": "B"}
        ],
    }
    response = client.post("/api/exercise/upload", json=payload, headers=teacher_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "Exercise set created"


def test_search_exercise_sets_returns_paginated_items(client, teacher_headers, db_session):
    course = db_session.query(Course).filter(Course.name == "Software Testing").first()
    assert course is not None

    client.post(
        "/api/exercise/upload",
        json={
            "course_id": course.id,
            "title": "Chapter 1 Quiz",
            "description": "basic questions",
            "questions": [
                {"type": "single", "question": "2+2=?", "options": ["3", "4", "5"], "answer": "B"}
            ],
        },
        headers=teacher_headers,
    )
    response = client.get(f"/api/exercise/search?course_id={course.id}&page=1&page_size=10", headers=teacher_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["total"] >= 1
    assert body["data"]["items"][0]["title"] == "Chapter 1 Quiz"


def test_get_exercise_detail_returns_question_set(client, teacher_headers, db_session):
    course = db_session.query(Course).filter(Course.name == "Software Testing").first()
    assert course is not None

    client.post(
        "/api/exercise/upload",
        json={
            "course_id": course.id,
            "title": "Detail Quiz",
            "description": "detail questions",
            "questions": [
                {"type": "single", "question": "2+2=?", "options": ["3", "4", "5"], "answer": "B"}
            ],
        },
        headers=teacher_headers,
    )
    exercise_set = db_session.query(ExerciseSet).filter(ExerciseSet.title == "Detail Quiz").first()
    assert exercise_set is not None

    response = client.get(f"/api/exercise/{exercise_set.id}", headers=teacher_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["title"] == "Detail Quiz"


def test_create_post_with_real_name_succeeds(client, teacher_headers, db_session):
    course = db_session.query(Course).filter(Course.name == "Software Testing").first()
    assert course is not None

    response = client.post(
        f"/api/course/{course.id}/post/create",
        json={"title": "Welcome", "content": "Hello class", "is_anonymous": False},
        headers=teacher_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["author"] == "teacher1"


def test_create_post_with_anonymous_name_succeeds(client, teacher_headers, db_session):
    course = db_session.query(Course).filter(Course.name == "Software Testing").first()
    assert course is not None

    response = client.post(
        f"/api/course/{course.id}/post/create",
        json={"title": "Anonymous", "content": "anonymous content", "is_anonymous": True},
        headers=teacher_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["author"] == "匿名"
    assert body["data"]["author_role"] is None


def test_get_posts_returns_paginated_post_list(client, teacher_headers, db_session):
    course = db_session.query(Course).filter(Course.name == "Software Testing").first()
    assert course is not None
    client.post(
        f"/api/course/{course.id}/post/create",
        json={"title": "Welcome", "content": "Hello class", "is_anonymous": False},
        headers=teacher_headers,
    )

    response = client.get(f"/api/course/{course.id}/post?skip=0&limit=10&keyword=Welcome", headers=teacher_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["total"] >= 1
    assert body["data"]["posts"][0]["title"] == "Welcome"


def test_empty_comment_is_rejected(client, teacher_headers, db_session):
    course = db_session.query(Course).filter(Course.name == "Software Testing").first()
    assert course is not None
    client.post(
        f"/api/course/{course.id}/post/create",
        json={"title": "Seed Post", "content": "Seed", "is_anonymous": False},
        headers=teacher_headers,
    )
    post = db_session.query(Post).filter(Post.title == "Seed Post").first()
    assert post is not None

    response = client.post(
        f"/api/course/posts/{post.id}/comments",
        json={"content": "   ", "parent_id": None, "is_anonymous": False},
        headers=teacher_headers,
    )

    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False
    assert body["message"] == "评论内容不能为空"


def test_reply_comment_succeeds(client, teacher_headers, student_headers, db_session):
    course = db_session.query(Course).filter(Course.name == "Software Testing").first()
    assert course is not None
    client.post(
        f"/api/course/{course.id}/post/create",
        json={"title": "Seed Post", "content": "Seed", "is_anonymous": False},
        headers=teacher_headers,
    )
    post = db_session.query(Post).filter(Post.title == "Seed Post").first()
    assert post is not None

    response = client.post(
        f"/api/course/posts/{post.id}/comments",
        json={"content": "I agree", "parent_id": 400, "is_anonymous": True},
        headers=student_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["parent_id"] == 400
    assert body["data"]["user"] == "匿名"


def test_get_comments_returns_comment_list(client, teacher_headers, student_headers, db_session):
    course = db_session.query(Course).filter(Course.name == "Software Testing").first()
    assert course is not None
    client.post(
        f"/api/course/{course.id}/post/create",
        json={"title": "Seed Post", "content": "Seed", "is_anonymous": False},
        headers=teacher_headers,
    )
    post = db_session.query(Post).filter(Post.title == "Seed Post").first()
    assert post is not None

    client.post(
        f"/api/course/posts/{post.id}/comments",
        json={"content": "This is a comment.", "parent_id": None, "is_anonymous": False},
        headers=student_headers,
    )
    response = client.get(f"/api/course/posts/{post.id}/comments?skip=0&limit=10", headers=teacher_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["total"] >= 1
    assert body["data"]["comments"][0]["content"] == "This is a comment."


def test_get_post_detail_returns_full_post(client, teacher_headers, db_session):
    course = db_session.query(Course).filter(Course.name == "Software Testing").first()
    assert course is not None
    client.post(
        f"/api/course/{course.id}/post/create",
        json={"title": "Detail Post", "content": "This is a post for black-box testing.", "is_anonymous": False},
        headers=teacher_headers,
    )
    post = db_session.query(Post).filter(Post.title == "Detail Post").first()
    assert post is not None

    response = client.get(f"/api/course/posts/{post.id}", headers=teacher_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["id"] == post.id
    assert body["data"]["content"] == "This is a post for black-box testing."
