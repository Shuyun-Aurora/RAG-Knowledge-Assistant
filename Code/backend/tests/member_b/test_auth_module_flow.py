from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi import FastAPI
from fastapi.testclient import TestClient

import controller.LoginController as login_controller
import controller.UserController as user_controller
from config.db import Base
import entity.User  # noqa: F401
import entity.UserAuth  # noqa: F401
import entity.Course  # noqa: F401
from entity.User import User
from entity.UserAuth import UserAuth
from util.jwt_utils import create_access_token


def _build_client():
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

    def _get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[login_controller.get_db] = _get_db
    app.dependency_overrides[user_controller.get_db] = _get_db
    return TestClient(app), TestingSessionLocal


def _register_and_login(client: TestClient, username: str, password: str, role: str = "student") -> str:
    reg = client.post("/api/register", json={"username": username, "password": password, "role": role})
    assert reg.status_code == 200
    assert reg.json()["success"] is True
    login = client.post("/api/login", json={"username": username, "password": password})
    assert login.status_code == 200
    return login.json()["data"]["token"]


def test_auth_flow_happy_path_and_profile_updates():
    client, _ = _build_client()
    token = _register_and_login(client, "alice", "pwd123")
    headers = {"Authorization": f"Bearer {token}"}

    me = client.get("/api/user/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["data"]["username"] == "alice"

    course_count = client.get("/api/user/course/count", headers=headers)
    assert course_count.status_code == 200
    assert course_count.json()["success"] is True

    change_pwd = client.put(
        "/api/user/password",
        json={"oldPassword": "pwd123", "newPassword": "new123"},
        headers=headers,
    )
    assert change_pwd.status_code == 200
    assert change_pwd.json()["success"] is True

    update_profile = client.put(
        "/api/user/profile",
        json={"name": "Alice", "email": "alice@example.com"},
        headers=headers,
    )
    assert update_profile.status_code == 200
    assert update_profile.json()["success"] is True

    old_login = client.post("/api/login", json={"username": "alice", "password": "pwd123"})
    assert old_login.status_code == 401
    new_login = client.post("/api/login", json={"username": "alice", "password": "new123"})
    assert new_login.status_code == 200


def test_auth_flow_invalid_and_conflict_paths():
    client, _ = _build_client()
    _register_and_login(client, "bob", "pwd123")

    unknown_login = client.post("/api/login", json={"username": "nobody", "password": "pwd123"})
    assert unknown_login.status_code == 401

    bad_login = client.post("/api/login", json={"username": "bob", "password": "bad"})
    assert bad_login.status_code == 401
    assert bad_login.json()["detail"] == "Invalid credentials"

    conflict_reg = client.post("/api/register", json={"username": "bob", "password": "pwd123", "role": "student"})
    assert conflict_reg.status_code == 200
    assert conflict_reg.json()["success"] is False


def test_auth_flow_token_and_password_error_paths():
    client, _ = _build_client()
    token = _register_and_login(client, "charlie", "pwd123")

    invalid_token_resp = client.get("/api/user/me", headers={"Authorization": "Bearer invalid.token.value"})
    assert invalid_token_resp.status_code == 401
    assert invalid_token_resp.json()["detail"] == "Invalid token"

    wrong_old_pwd = client.put(
        "/api/user/password",
        json={"oldPassword": "wrong-old", "newPassword": "new123"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert wrong_old_pwd.status_code == 200
    assert wrong_old_pwd.json()["success"] is False
    assert wrong_old_pwd.json()["message"] == "旧密码错误"


def test_auth_flow_user_not_found_and_auth_missing_path():
    client, session_factory = _build_client()

    with session_factory() as db:
        user = User(username="ghost", role="student", email="ghost@example.com", name="Ghost")
        db.add(user)
        db.commit()
        db.refresh(user)
        ghost_id = user.id

    ghost_token = create_access_token({"sub": str(ghost_id)})

    with session_factory() as db:
        db.query(User).filter(User.id == ghost_id).delete()
        db.commit()

    no_user_resp = client.get("/api/user/me", headers={"Authorization": f"Bearer {ghost_token}"})
    assert no_user_resp.status_code == 401
    assert no_user_resp.json()["detail"] == "User not found"

    token = _register_and_login(client, "noauth", "pwd123")
    with session_factory() as db:
        user = db.query(User).filter(User.username == "noauth").first()
        db.query(UserAuth).filter(UserAuth.user_id == user.id).delete()
        db.commit()

    no_auth_resp = client.put(
        "/api/user/password",
        json={"oldPassword": "pwd123", "newPassword": "new123"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert no_auth_resp.status_code == 200
    assert no_auth_resp.json()["success"] is False
    assert no_auth_resp.json()["message"] == "用户认证信息不存在"


def test_auth_flow_update_profile_exception_path():
    client, _ = _build_client()
    token_a = _register_and_login(client, "u_a", "pwd123")
    token_b = _register_and_login(client, "u_b", "pwd123")

    set_b = client.put(
        "/api/user/profile",
        json={"name": "B", "email": "dup@example.com"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert set_b.status_code == 200
    assert set_b.json()["success"] is True

    # email 唯一约束冲突，触发 update_profile_service 的 except 分支
    bad_update = client.put(
        "/api/user/profile",
        json={"name": "A", "email": "dup@example.com"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert bad_update.status_code == 200
    assert bad_update.json()["success"] is False

