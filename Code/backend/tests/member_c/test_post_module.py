import pytest

from entity.Comment import Comment
from entity.Post import Post


def test_get_course_posts_returns_paginated_posts(client, course_1, post_bundle):
    response = client.get(
        f"/api/course/{course_1.id}/post",
        params={"skip": 0, "limit": 10, "keyword": ""},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["total"] == 2
    assert len(body["data"]["posts"]) == 2
    assert body["data"]["posts"][0]["title"] == post_bundle["post_anon"].title
    assert body["data"]["posts"][0]["author"] == "匿名"
    assert body["data"]["posts"][0]["author_role"] is None
    assert body["data"]["posts"][1]["author"] == "student_user"
    assert body["data"]["posts"][1]["author_role"] == "student"


def test_get_course_posts_filters_by_trimmed_keyword(client, course_1, post_bundle):
    response = client.get(
        f"/api/course/{course_1.id}/post",
        params={"skip": 0, "limit": 10, "keyword": "  作业  "},
    )

    assert response.status_code == 200
    posts = response.json()["data"]["posts"]
    assert len(posts) == 2
    assert all("作业" in (post["title"] + post["content"]) for post in posts)


def test_create_post_success_for_real_name(client, login_as, student_user, db_session, course_1):
    login_as(student_user)

    response = client.post(
        f"/api/course/{course_1.id}/post/create",
        json={"title": "讨论帖", "content": "这里是正文", "is_anonymous": False},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["author"] == student_user.username
    assert body["data"]["author_role"] == student_user.role
    assert db_session.query(Post).filter(Post.title == "讨论帖").first() is not None


def test_create_post_success_for_anonymous_user(client, login_as, teacher_user, db_session, course_1):
    login_as(teacher_user)

    response = client.post(
        f"/api/course/{course_1.id}/post/create",
        json={"title": "匿名帖", "content": "匿名内容", "is_anonymous": True},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["author"] == "匿名"
    assert body["data"]["author_role"] is None
    created = db_session.query(Post).filter(Post.title == "匿名帖").first()
    assert created is not None
    assert created.is_anonymous is True


def test_get_comments_returns_sorted_comment_list(client, post_bundle):
    response = client.get(
        f"/api/course/posts/{post_bundle['post_real'].id}/comments",
        params={"skip": 0, "limit": 10},
    )

    assert response.status_code == 200
    body = response.json()
    comments = body["data"]["comments"]
    assert body["data"]["total"] == 2
    assert comments[0]["content"] == "这是一级评论"
    assert comments[0]["parent_id"] is None
    assert comments[1]["content"] == "这是回复评论"
    assert comments[1]["parent_id"] == post_bundle["comment_parent"].id


def test_add_comment_rejects_blank_content(client, login_as, student_user, post_bundle):
    login_as(student_user)

    response = client.post(
        f"/api/course/posts/{post_bundle['post_real'].id}/comments",
        json={"content": "   ", "parent_id": None, "is_anonymous": False},
    )

    assert response.status_code == 400
    assert response.json()["message"] == "评论内容不能为空"


def test_add_comment_success(client, login_as, student_user, db_session, post_bundle):
    login_as(student_user)

    response = client.post(
        f"/api/course/posts/{post_bundle['post_real'].id}/comments",
        json={"content": "这是一条普通评论", "parent_id": None, "is_anonymous": False},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "评论成功"
    assert body["data"]["parent_id"] is None
    created = db_session.query(Comment).filter(Comment.content == "这是一条普通评论").first()
    assert created is not None


def test_add_reply_comment_success(client, login_as, teacher_user, db_session, post_bundle):
    login_as(teacher_user)

    response = client.post(
        f"/api/course/posts/{post_bundle['post_real'].id}/comments",
        json={
            "content": "这是回复",
            "parent_id": post_bundle["comment_parent"].id,
            "is_anonymous": False,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["parent_id"] == post_bundle["comment_parent"].id
    created = db_session.query(Comment).filter(Comment.content == "这是回复").first()
    assert created.parent_id == post_bundle["comment_parent"].id


def test_add_anonymous_comment_success(client, login_as, teacher_user, db_session, post_bundle):
    login_as(teacher_user)

    response = client.post(
        f"/api/course/posts/{post_bundle['post_real'].id}/comments",
        json={"content": "匿名评论", "parent_id": None, "is_anonymous": True},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["user"] == "匿名"
    assert body["data"]["user_role"] is None
    created = db_session.query(Comment).filter(Comment.content == "匿名评论").first()
    assert created.is_anonymous is True


def test_get_post_by_id_success(client, post_bundle):
    response = client.get(f"/api/course/posts/{post_bundle['post_real'].id}")

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["id"] == post_bundle["post_real"].id
    assert body["data"]["title"] == post_bundle["post_real"].title
    assert body["data"]["author"] == "student_user"


def test_get_post_by_id_returns_404_when_missing(client):
    response = client.get("/api/course/posts/999999")

    assert response.status_code == 404
    assert response.json()["message"] == "帖子不存在"


def test_add_comment_should_reject_missing_post(client, login_as, student_user):
    login_as(student_user)

    response = client.post(
        "/api/course/posts/999999/comments",
        json={"content": "无效帖子评论", "parent_id": None, "is_anonymous": False},
    )

    assert response.status_code in {400, 404}


def test_add_comment_should_reject_missing_parent(client, login_as, student_user, post_bundle):
    login_as(student_user)

    response = client.post(
        f"/api/course/posts/{post_bundle['post_real'].id}/comments",
        json={"content": "回复不存在的父评论", "parent_id": 999999, "is_anonymous": False},
    )

    assert response.status_code in {400, 404}
