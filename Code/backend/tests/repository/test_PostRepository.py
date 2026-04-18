import pytest
from unittest.mock import Mock
from sqlalchemy.orm import Session
from datetime import datetime

from repository.PostRepository import (
    create_post, get_post_by_id,
    get_posts_by_course_paginated, count_posts_by_course
)


# ------------ 假对象 ------------
class FakeUser:
    def __init__(self, id=1, username="test_user"):
        self.id = id
        self.username = username

class FakePost:
    def __init__(self, id=1, title="Test Post", content="Test Content",
                 user_id=1, course_id=1, author=None):
        self.id = id
        self.title = title
        self.content = content
        self.user_id = user_id
        self.course_id = course_id
        self.author = author or FakeUser()


# ------------ fixture ------------
@pytest.fixture
def mock_db():
    return Mock(spec=Session)


# ------------ create_post ------------
def test_create_post_success(mock_db, monkeypatch):
    fake_post = FakePost()
    monkeypatch.setattr("repository.PostRepository.Post", lambda **kwargs: fake_post)

    mock_db.add = Mock()
    mock_db.commit = Mock()
    mock_db.refresh = Mock()

    result = create_post(mock_db, 1, 1, "Test Post", "Test Content", False)

    assert result == fake_post
    mock_db.add.assert_called_once_with(fake_post)
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(fake_post)


# ------------ get_post_by_id ------------
def test_get_post_by_id_success(mock_db):
    fake_post = FakePost()
    mock_query = Mock()
    mock_filter = Mock()

    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    mock_filter.first.return_value = fake_post

    result = get_post_by_id(mock_db, 1)
    assert result == fake_post

def test_get_post_by_id_not_found(mock_db):
    mock_query = Mock()
    mock_filter = Mock()

    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    mock_filter.first.return_value = None

    result = get_post_by_id(mock_db, 999)
    assert result is None


# ------------ get_posts_by_course_paginated ------------
def test_get_posts_by_course_paginated(mock_db):
    fake_posts = [FakePost(), FakePost(id=2)]

    mock_query = Mock()
    mock_filtered = Mock()
    mock_ordered = Mock()
    mock_offset = Mock()
    mock_limit = Mock()
    mock_limit.all.return_value = fake_posts

    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filtered
    mock_filtered.order_by.return_value = mock_ordered
    mock_ordered.offset.return_value = mock_offset
    mock_offset.limit.return_value = mock_limit

    result = get_posts_by_course_paginated(mock_db, 1, skip=0, limit=10, keyword="")
    assert result == fake_posts


# ------------ count_posts_by_course ------------
def test_count_posts_by_course(mock_db):
    mock_query = Mock()
    mock_filtered = Mock()
    mock_filtered.count.return_value = 3

    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filtered

    result = count_posts_by_course(mock_db, 1, keyword="")
    assert result == 3

def test_get_posts_by_course_paginated_with_keyword(mock_db):
    fake_posts = [FakePost(), FakePost(id=2)]

    mock_query = Mock()
    mock_filtered1 = Mock()
    mock_filtered2 = Mock()
    mock_ordered = Mock()
    mock_offset = Mock()
    mock_limit = Mock()
    mock_limit.all.return_value = fake_posts

    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filtered1
    # 关键：keyword 分支会再次 filter
    mock_filtered1.filter.return_value = mock_filtered2
    mock_filtered2.order_by.return_value = mock_ordered
    mock_ordered.offset.return_value = mock_offset
    mock_offset.limit.return_value = mock_limit

    result = get_posts_by_course_paginated(mock_db, 1, skip=0, limit=10, keyword="hello")
    assert result == fake_posts
    mock_query.filter.assert_called_once()  # 第一次 filter(course_id)
    mock_filtered1.filter.assert_called_once()  # 第二次 filter(keyword)

def test_count_posts_by_course_with_keyword(mock_db):
    mock_query = Mock()
    mock_filtered1 = Mock()
    mock_filtered2 = Mock()
    mock_filtered2.count.return_value = 5

    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filtered1
    mock_filtered1.filter.return_value = mock_filtered2

    result = count_posts_by_course(mock_db, 1, keyword="hello")
    assert result == 5
    mock_query.filter.assert_called_once()
    mock_filtered1.filter.assert_called_once()