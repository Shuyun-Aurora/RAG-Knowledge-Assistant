import pytest
from fastapi import FastAPI 
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from main import app
from controller import LoginController
from controller.LoginController import router

@pytest.fixture
def app_instance():
    app = FastAPI()
    # mock get_db 依赖，返回 MagicMock
    app.dependency_overrides[LoginController.get_db] = lambda: MagicMock()
    app.include_router(LoginController.router)
    return app

@pytest.fixture
def client(app_instance):
    return TestClient(app_instance)

@patch("controller.LoginController.verify_login")
@patch("util.jwt_utils.create_access_token", return_value="token123")
def test_login_success(mock_create_token, mock_verify_login, client):
    user = MagicMock(id=1)
    mock_verify_login.return_value = user
    response = client.post("/login", json={"username": "alice", "password": "pw"})
    print(response.json())
    assert response.status_code == 200

@patch("service.LoginService.verify_login")
def test_login_fail(mock_verify_login, client):
    mock_verify_login.return_value = None
    response = client.post("/login", json={"username": "alice", "password": "wrong"})
    assert response.status_code == 401
    data = response.json()
    assert data.get("detail") == "Invalid credentials" or data.get("message") == "Invalid credentials"

@patch("controller.LoginController.register_user")
def test_register_success(mock_register_user, client):
    mock_register_user.return_value = MagicMock(id=2)
    response = client.post("/register", json={"username": "bob", "password": "pw", "role": "student"})
    print(response.json())
    data = response.json()
    assert data["success"] is True

@patch("service.LoginService.register_user", side_effect=ValueError("Username already exists"))
def test_register_username_exists(mock_register_user, client):
    response = client.post("/register", json={"username": "bob", "password": "pw", "role": "student"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["message"] == "Username already exists" 