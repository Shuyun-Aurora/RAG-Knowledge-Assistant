import pytest
from unittest.mock import Mock
from sqlalchemy.orm import Session
from datetime import datetime

from repository.CommentRepository import add_comment, get_comments_by_post


# -------------------- 假数据结构 --------------------
class FakeUser:
    def __init__(self, id=1, username="test_user"):
        self.id = id
        self.username = username

class FakeComment:
    def __init__(self, id=1, content="Test Comment", user_id=1, post_id=1, author=None):
        self.id = id
        self.content = content
        self.user_id = user_id
        self.post_id = post_id
        self.author = author or FakeUser()


# -------------------- pytest fixtures --------------------
@pytest.fixture
def mock_db():
    return Mock(spec=Session)


# -------------------- add_comment --------------------
def test_add_comment_success(mock_db, monkeypatch):
    fake_comment = FakeComment()

    # Patch Comment 构造函数为返回假对象
    monkeypatch.setattr("repository.CommentRepository.Comment", lambda **kwargs: fake_comment)

    mock_db.add = Mock()
    mock_db.commit = Mock()
    mock_db.refresh = Mock()

    result = add_comment(
        db=mock_db,
        post_id=1,
        user_id=1,
        content="Test Comment",
        created_at=datetime.now()
    )

    assert result == fake_comment
    mock_db.add.assert_called_once_with(fake_comment)
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(fake_comment)


# -------------------- get_comments_by_post: 有结果 --------------------
def test_get_comments_by_post_success(mock_db):
    fake_comments = [FakeComment(), FakeComment(id=2)]

    # 模拟 SQLAlchemy 查询链条
    mock_query = Mock()
    mock_filter = Mock()
    mock_order = Mock()
    mock_offset = Mock()
    mock_limit = Mock()

    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    mock_filter.order_by.return_value = mock_order
    mock_order.count.return_value = 2
    mock_order.offset.return_value = mock_offset
    mock_offset.limit.return_value = mock_limit
    mock_limit.all.return_value = fake_comments

    result = get_comments_by_post(
        db=mock_db,
        post_id=1,
        skip=0,
        limit=10
    )

    assert result == {"total": 2, "comments": fake_comments}


# -------------------- get_comments_by_post: 空结果 --------------------
def test_get_comments_by_post_empty(mock_db):
    # 模拟 SQLAlchemy 查询链条返回空
    mock_query = Mock()
    mock_filter = Mock()
    mock_order = Mock()
    mock_offset = Mock()
    mock_limit = Mock()

    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    mock_filter.order_by.return_value = mock_order
    mock_order.count.return_value = 0
    mock_order.offset.return_value = mock_offset
    mock_offset.limit.return_value = mock_limit
    mock_limit.all.return_value = []

    result = get_comments_by_post(
        db=mock_db,
        post_id=999,
        skip=0,
        limit=10
    )

    assert result == {"total": 0, "comments": []}
