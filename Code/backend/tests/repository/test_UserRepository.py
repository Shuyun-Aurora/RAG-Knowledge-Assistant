import pytest
from unittest.mock import Mock, MagicMock
from sqlalchemy.orm import Session
from repository.UserRepository import (
    get_user_by_username, create_user, get_user_by_id, 
    get_auth_by_user_id, save_user, update_user_profile
)

class FakeUser:
    def __init__(self, id=1, username="test", role="student", name="Test User", email="test@example.com"):
        self.id = id
        self.username = username
        self.role = role
        self.name = name
        self.email = email

class FakeUserAuth:
    def __init__(self, user_id=1, hashed_password="hashed"):
        self.user_id = user_id
        self.hashed_password = hashed_password

@pytest.fixture
def mock_db():
    return Mock(spec=Session)

# ---------- get_user_by_username ----------
def test_get_user_by_username_success(mock_db):
    fake_user = FakeUser()
    mock_query = Mock()
    mock_filter = Mock()
    mock_first = Mock(return_value=fake_user)
    
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    mock_filter.first.return_value = fake_user
    
    result = get_user_by_username(mock_db, "test")
    
    assert result == fake_user
    mock_db.query.assert_called_once()
    mock_query.filter.assert_called_once()

def test_get_user_by_username_not_found(mock_db):
    mock_query = Mock()
    mock_filter = Mock()
    mock_first = Mock(return_value=None)
    
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    mock_filter.first.return_value = None
    
    result = get_user_by_username(mock_db, "nonexistent")
    
    assert result is None

# ---------- create_user ----------
def test_create_user_success(mock_db):
    fake_user = FakeUser()
    mock_db.add = Mock()
    mock_db.flush = Mock()
    
    # Mock User class
    with pytest.MonkeyPatch().context() as m:
        m.setattr("repository.UserRepository.User", lambda **kwargs: fake_user)
        result = create_user(mock_db, "test", "student")
    
    assert result == fake_user
    mock_db.add.assert_called_once_with(fake_user)
    mock_db.flush.assert_called_once()

# ---------- get_user_by_id ----------
def test_get_user_by_id_success(mock_db):
    fake_user = FakeUser()
    mock_query = Mock()
    mock_filter = Mock()
    mock_first = Mock(return_value=fake_user)
    
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    mock_filter.first.return_value = fake_user
    
    result = get_user_by_id(mock_db, 1)
    
    assert result == fake_user

def test_get_user_by_id_not_found(mock_db):
    mock_query = Mock()
    mock_filter = Mock()
    mock_first = Mock(return_value=None)
    
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    mock_filter.first.return_value = None
    
    result = get_user_by_id(mock_db, 999)
    
    assert result is None

# ---------- get_auth_by_user_id ----------
def test_get_auth_by_user_id_success(mock_db):
    fake_auth = FakeUserAuth()
    mock_query = Mock()
    mock_filter = Mock()
    mock_first = Mock(return_value=fake_auth)
    
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    mock_filter.first.return_value = fake_auth
    
    result = get_auth_by_user_id(mock_db, 1)
    
    assert result == fake_auth

def test_get_auth_by_user_id_not_found(mock_db):
    mock_query = Mock()
    mock_filter = Mock()
    mock_first = Mock(return_value=None)
    
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    mock_filter.first.return_value = None
    
    result = get_auth_by_user_id(mock_db, 999)
    
    assert result is None

# ---------- save_user ----------
def test_save_user_success(mock_db):
    fake_user = FakeUser()
    mock_db.add = Mock()
    mock_db.commit = Mock()
    mock_db.refresh = Mock()
    
    save_user(mock_db, fake_user)
    
    mock_db.add.assert_called_once_with(fake_user)
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(fake_user)

# ---------- update_user_profile ----------
def test_update_user_profile_success(mock_db):
    fake_user = FakeUser()
    mock_query = Mock()
    mock_filter = Mock()
    mock_first = Mock(return_value=fake_user)
    
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    mock_filter.first.return_value = fake_user
    mock_db.commit = Mock()
    mock_db.refresh = Mock()
    
    update_user_profile(mock_db, 1, "New Name", "new@example.com")
    
    assert fake_user.name == "New Name"
    assert fake_user.email == "new@example.com"
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(fake_user)

def test_update_user_profile_user_not_found(mock_db):
    mock_query = Mock()
    mock_filter = Mock()
    mock_first = Mock(return_value=None)
    
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    mock_filter.first.return_value = None
    
    with pytest.raises(Exception, match="用户不存在"):
        update_user_profile(mock_db, 999, "New Name", "new@example.com") 