import pytest
from unittest.mock import Mock
from sqlalchemy.orm import Session
from repository.UserAuthRepository import create_user_auth, get_auth_by_user_id, save_user_auth

class FakeUserAuth:
    def __init__(self, user_id=1, hashed_password="hashed"):
        self.user_id = user_id
        self.hashed_password = hashed_password

@pytest.fixture
def mock_db():
    return Mock(spec=Session)

# ---------- create_user_auth ----------
def test_create_user_auth_success(mock_db):
    mock_db.add = Mock()
    
    # Mock UserAuth class
    with pytest.MonkeyPatch().context() as m:
        m.setattr("repository.UserAuthRepository.UserAuth", lambda **kwargs: FakeUserAuth(**kwargs))
        create_user_auth(mock_db, 1, "hashed_password")
    
    mock_db.add.assert_called_once()
    # 验证传入的参数
    call_args = mock_db.add.call_args[0][0]
    assert call_args.user_id == 1
    assert call_args.hashed_password == "hashed_password"

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
    mock_db.query.assert_called_once()

def test_get_auth_by_user_id_not_found(mock_db):
    mock_query = Mock()
    mock_filter = Mock()
    mock_first = Mock(return_value=None)
    
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    mock_filter.first.return_value = None
    
    result = get_auth_by_user_id(mock_db, 999)
    
    assert result is None

# ---------- save_user_auth ----------
def test_save_user_auth_success(mock_db):
    fake_auth = FakeUserAuth()
    mock_db.add = Mock()
    mock_db.commit = Mock()
    mock_db.refresh = Mock()
    
    save_user_auth(mock_db, fake_auth)
    
    mock_db.add.assert_called_once_with(fake_auth)
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(fake_auth) 