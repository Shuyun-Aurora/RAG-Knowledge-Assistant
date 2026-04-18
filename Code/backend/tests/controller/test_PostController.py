import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from datetime import datetime
from main import app
from controller import PostController

client = TestClient(app)

# ---------- GET /{course_id}/post ----------
@patch("controller.PostController.fetch_course_posts")
def test_get_course_posts(mock_fetch_course_posts):
    mock_fetch_course_posts.return_value = {
        "total": 1,
        "posts": [
            type("Post", (), {
                "id": 123,
                "title": "Test Post",
                "content": "Content",
                "is_anonymous": False,
                "created_at": datetime.utcnow(),
                "user": type("User", (), {"username": "Alice"})()
            })()
        ]
    }
    response = client.get("/api/course/1/post?skip=0&limit=10&keyword=")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["data"]["total"] == 1
    assert json_data["data"]["posts"][0]["author"] == "Alice"

# ---------- POST /{course_id}/post/create ----------
def override_get_current_user():
    return type("User", (), {"id": 1, "username": "Bob"})()

@patch("controller.PostController.publish_post")
def test_create_post(mock_publish_post):
    app.dependency_overrides[PostController.get_current_user] = override_get_current_user
    mock_publish_post.return_value = type("Post", (), {
        "id": 456,
        "title": "New Post",
        "content": "Post content",
        "is_anonymous": False,
        "created_at": datetime.utcnow(),
        "user": type("User", (), {"username": "Bob"})()
    })()
    response = client.post(
        "/api/course/1/post/create",
        json={
            "title": "New Post",
            "content": "Post content",
            "is_anonymous": False
        }
    )
    assert response.status_code == 200
    assert response.json()["data"]["author"] == "Bob"
    app.dependency_overrides = {}

# ---------- GET /posts/{post_id}/comments ----------
@patch("controller.PostController.get_post_comments")
def test_get_comments(mock_get_post_comments):
    mock_get_post_comments.return_value = {
        "total": 1,
        "comments": [
            type("Comment", (), {
                "id": 1,
                "content": "Comment content",
                "is_anonymous": False,
                "created_at": datetime.utcnow(),
                "parent_id": None,
                "user": type("User", (), {"username": "Charlie"})()
            })()
        ]
    }
    response = client.get("/api/course/posts/123/comments")
    assert response.status_code == 200
    assert response.json()["data"]["comments"][0]["user"] == "Charlie"

# ---------- POST /posts/{post_id}/comments ----------
def override_get_current_user_eve():
    return type("User", (), {"id": 2, "username": "Eve"})()

@patch("controller.PostController.create_comment")
def test_add_comment(mock_create_comment):
    app.dependency_overrides[PostController.get_current_user] = override_get_current_user_eve
    mock_create_comment.return_value = type("Comment", (), {
        "id": 99,
        "content": "Reply content",
        "is_anonymous": False,
        "created_at": datetime.utcnow(),
        "parent_id": None,
        "user": type("User", (), {"username": "Eve"})()
    })()
    response = client.post(
        "/api/course/posts/123/comments",
        json={
            "content": "Reply content",
            "is_anonymous": False,
            "parent_id": None
        }
    )
    assert response.status_code == 200
    assert response.json()["data"]["content"] == "Reply content"
    app.dependency_overrides = {}

def test_add_comment_empty_content():
    app.dependency_overrides[PostController.get_current_user] = override_get_current_user_eve
    response = client.post(
        "/api/course/posts/123/comments",
        json={
            "content": "   ",  # 只包含空格
            "is_anonymous": False,
            "parent_id": None
        }
    )
    assert response.status_code == 400
    data = response.json()
    assert data.get("message") == "评论内容不能为空"
    app.dependency_overrides = {}

# ---------- GET /posts/{post_id} ----------
@patch("controller.PostController.fetch_post_by_id")
def test_get_post_by_id(mock_fetch_post_by_id):
    mock_fetch_post_by_id.return_value = type("Post", (), {
        "id": 789,
        "title": "Single Post",
        "content": "One content",
        "is_anonymous": False,
        "created_at": datetime.utcnow(),
        "user": type("User", (), {"username": "David"})()
    })()
    response = client.get("/api/course/posts/789")
    assert response.status_code == 200
    assert response.json()["data"]["author"] == "David"

@patch("controller.PostController.fetch_post_by_id")
def test_get_post_by_id_not_found(mock_fetch_post_by_id):
    mock_fetch_post_by_id.return_value = None  # 模拟查不到
    response = client.get("/api/course/posts/99999")
    assert response.status_code == 404
    data = response.json()
    assert data.get("message") == "帖子不存在"
