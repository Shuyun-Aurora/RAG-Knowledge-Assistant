def test_register_success_returns_success_message(client, db_session):
    response = client.post(
        "/api/register",
        json={"username": "new_user", "password": "Pass123!", "role": "teacher"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "Register successful"

    from entity.User import User

    created_user = db_session.query(User).filter(User.username == "new_user").first()
    assert created_user is not None
    assert created_user.role == "teacher"


def test_register_duplicate_username_returns_failure(client):
    response = client.post(
        "/api/register",
        json={"username": "teacher1", "password": "Pass123!", "role": "teacher"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is False
    assert "exists" in body["message"]


def test_login_success_returns_token(client):
    response = client.post(
        "/api/login",
        json={"username": "teacher1", "password": "Pass123!"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["token"]


def test_login_with_invalid_credentials_returns_401(client):
    response = client.post(
        "/api/login",
        json={"username": "teacher1", "password": "wrong-password"},
    )

    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["message"] == "Invalid credentials"


def test_get_me_returns_current_user_profile(client, student_headers):
    response = client.get("/api/user/me", headers=student_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["username"] == "student1"
    assert body["data"]["role"] == "student"


def test_update_profile_with_valid_email_succeeds(client, teacher_headers):
    response = client.put(
        "/api/user/profile",
        json={"name": "Teacher Updated", "email": "teacher.updated@example.com"},
        headers=teacher_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "资料更新成功"

    me_response = client.get("/api/user/me", headers=teacher_headers)
    me_body = me_response.json()
    assert me_body["data"]["name"] == "Teacher Updated"
    assert me_body["data"]["email"] == "teacher.updated@example.com"


def test_update_profile_with_invalid_email_is_rejected(client, teacher_headers):
    response = client.put(
        "/api/user/profile",
        json={"name": "Teacher Updated", "email": "invalid-email"},
        headers=teacher_headers,
    )

    assert response.status_code == 422
