from entity.Course import Course


def test_student_cannot_create_course(client, student_headers):
    response = client.post(
        "/api/course/create",
        json={"name": "Software Testing", "description": "black-box testing course"},
        headers=student_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is False
    assert "Only teachers" in body["message"]


def test_teacher_can_create_new_course(client, teacher_headers):
    response = client.post(
        "/api/course/create",
        json={"name": "Newly Created Course", "description": "teacher created course"},
        headers=teacher_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["name"] == "Newly Created Course"


def test_get_all_courses_returns_paginated_data(client, teacher_headers):
    response = client.get("/api/course/all?page=1&page_size=12&keyword=Software", headers=teacher_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["total"] >= 1
    assert body["data"]["courses"][0]["name"] == "Software Testing"


def test_get_all_courses_supports_keyword_search(client, teacher_headers):
    client.post(
        "/api/course/create",
        json={"name": "Keyword Matched Course", "description": "search target"},
        headers=teacher_headers,
    )

    response = client.get("/api/course/all?page=1&page_size=12&keyword=Keyword", headers=teacher_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["courses"][0]["name"] == "Keyword Matched Course"


def test_student_can_join_course(client, teacher_headers, student_headers):
    create_response = client.post(
        "/api/course/create",
        json={"name": "Joinable Course", "description": "join this course"},
        headers=teacher_headers,
    )
    course_id = create_response.json()["data"]["id"]

    response = client.post(f"/api/course/join/{course_id}", headers=student_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["id"] == course_id


def test_teacher_cannot_join_course(client, teacher_headers):
    response = client.post("/api/course/join/1", headers=teacher_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is False
    assert "Only students" in body["message"]


def test_student_can_quit_joined_course(client, student_headers, db_session):
    course = db_session.query(Course).filter(Course.name == "Software Testing").first()
    assert course is not None

    response = client.post(f"/api/course/quit/{course.id}", headers=student_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["id"] == course.id


def test_teacher_can_dissolve_own_course(client, teacher_headers, db_session):
    course = db_session.query(Course).filter(Course.name == "Software Testing").first()
    assert course is not None

    response = client.post(f"/api/course/dissolve/{course.id}", headers=teacher_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["is_deleted"] is True


def test_student_can_view_joined_courses(client, student_headers):
    response = client.get("/api/course/join?page=1&page_size=12&keyword=", headers=student_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["total"] >= 1


def test_teacher_can_view_taught_courses(client, teacher_headers):
    response = client.get("/api/course/teach?page=1&page_size=12&keyword=", headers=teacher_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["total"] >= 1


def test_get_course_detail_returns_course_info(client, teacher_headers, db_session):
    course = db_session.query(Course).filter(Course.name == "Software Testing").first()
    assert course is not None

    response = client.get(f"/api/course/{course.id}", headers=teacher_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["description"] == "default course"
