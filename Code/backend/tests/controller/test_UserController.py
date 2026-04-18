import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from types import SimpleNamespace
from controller.UserController import router
from service.UserService import get_current_user
from config.db import get_db

app = FastAPI()
app.include_router(router)
client = TestClient(app)

def override_user():
    return SimpleNamespace(id=1, username="alice", email="a@b.com", name="Alice", role="student")

def override_db():
    return MagicMock()

# ---------- GET /me ----------
def test_get_me():
    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_db] = override_db
    response = client.get("/me", headers={"Authorization": "Bearer token"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["username"] == "alice"
    app.dependency_overrides = {}

# ---------- PUT /password ----------
@patch("controller.UserController.change_password_service", return_value=(True, "修改成功"))
def test_change_password_success(mock_change):
    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_db] = override_db
    response = client.put("/password", json={"oldPassword": "old", "newPassword": "new"}, headers={"Authorization": "Bearer token"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["message"] == "密码修改成功"
    app.dependency_overrides = {}

@patch("controller.UserController.change_password_service", return_value=(False, "旧密码错误"))
def test_change_password_fail(mock_change):
    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_db] = override_db
    response = client.put("/password", json={"oldPassword": "old", "newPassword": "new"}, headers={"Authorization": "Bearer token"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["message"] == "旧密码错误"
    app.dependency_overrides = {}

# ---------- PUT /profile ----------
@patch("controller.UserController.update_profile_service", return_value=(True, "资料更新成功"))
def test_update_profile_success(mock_update):
    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_db] = override_db
    response = client.put("/profile", json={"name": "Alice", "email": "a@b.com"}, headers={"Authorization": "Bearer token"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["message"] == "资料更新成功"
    app.dependency_overrides = {}

@patch("controller.UserController.update_profile_service", return_value=(False, "邮箱已存在"))
def test_update_profile_fail(mock_update):
    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_db] = override_db
    response = client.put("/profile", json={"name": "Alice", "email": "test@a.com"}, headers={"Authorization": "Bearer token"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["message"] == "邮箱已存在"
    app.dependency_overrides = {}

def test_update_profile_invalid_email():
    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_db] = override_db
    response = client.put("/profile", json={"name": "Alice", "email": "bademail"}, headers={"Authorization": "Bearer token"})
    assert response.status_code == 422
    app.dependency_overrides = {}