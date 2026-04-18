import pytest
from unittest.mock import Mock
from sqlalchemy.orm import Session
from repository.CourseRepository import (
    get_all_courses, get_course_by_id, get_joined_courses_by_user_id,
    get_courses_by_teacher_id, save_course, get_course_by_name, dissolve_course
)

class FakeCourse:
    def __init__(self, id=1, name="Test Course", description="Test Description", 
                 teacher_id=1, is_deleted=False, teacher=None):
        self.id = id
        self.name = name
        self.description = description
        self.teacher_id = teacher_id
        self.is_deleted = is_deleted
        self.teacher = teacher or FakeUser()

class FakeUser:
    def __init__(self, id=1, username="teacher", role="teacher"):
        self.id = id
        self.username = username
        self.role = role
        self.joined_courses = []

@pytest.fixture
def mock_db():
    return Mock(spec=Session)

# ---------- get_all_courses ----------
def test_get_all_courses_basic(mock_db):
    fake_courses = [FakeCourse(), FakeCourse(id=2)]
    mock_query = Mock()
    mock_options = Mock()
    # 关键：filter/offset/limit 返回自身，支持链式调用
    mock_options.filter.return_value = mock_options
    mock_options.offset.return_value = mock_options
    mock_options.limit.return_value = mock_options
    mock_options.count.return_value = 2
    mock_options.all.return_value = fake_courses

    mock_db.query.return_value = mock_query
    mock_query.options.return_value = mock_options

    result, total = get_all_courses(mock_db, 1, 10, '', False)

    assert result == fake_courses
    assert total == 2

def test_get_all_courses_with_keyword(mock_db):
    fake_courses = [FakeCourse()]
    mock_query = Mock()
    mock_options = Mock()
    mock_filter = Mock()
    mock_join = Mock()
    mock_count = Mock(return_value=1)
    mock_offset = Mock()
    mock_limit = Mock()
    mock_all = Mock(return_value=fake_courses)
    
    mock_db.query.return_value = mock_query
    mock_query.options.return_value = mock_options
    mock_options.filter.return_value = mock_filter
    mock_filter.join.return_value = mock_join
    mock_join.filter.return_value = mock_filter
    mock_filter.count.return_value = 1
    mock_filter.offset.return_value = mock_offset
    mock_offset.limit.return_value = mock_limit
    mock_limit.all.return_value = fake_courses
    
    result, total = get_all_courses(mock_db, 1, 10, 'test', False)
    
    assert result == fake_courses
    assert total == 1

# ---------- get_course_by_id ----------
def test_get_course_by_id_success(mock_db):
    fake_course = FakeCourse()
    mock_query = Mock()
    mock_filter = Mock()
    mock_first = Mock(return_value=fake_course)
    
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    mock_filter.first.return_value = fake_course
    
    result = get_course_by_id(mock_db, 1)
    
    assert result == fake_course

def test_get_course_by_id_not_found(mock_db):
    mock_query = Mock()
    mock_filter = Mock()
    mock_first = Mock(return_value=None)
    
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    mock_filter.first.return_value = None
    
    result = get_course_by_id(mock_db, 999)
    
    assert result is None

# ---------- get_joined_courses_by_user_id ----------
def test_get_joined_courses_by_user_id_success(mock_db):
    fake_user = FakeUser()
    fake_user.joined_courses = [FakeCourse(), FakeCourse(id=2)]
    mock_query = Mock()
    mock_options = Mock()
    mock_get = Mock(return_value=fake_user)
    
    mock_db.query.return_value = mock_query
    mock_query.options.return_value = mock_options
    mock_options.get.return_value = fake_user
    
    result, total = get_joined_courses_by_user_id(mock_db, 1, 1, 10, '', True)
    
    assert result == fake_user.joined_courses
    assert total == 2

def test_get_joined_courses_by_user_id_user_not_found(mock_db):
    mock_query = Mock()
    mock_options = Mock()
    mock_get = Mock(return_value=None)
    
    mock_db.query.return_value = mock_query
    mock_query.options.return_value = mock_options
    mock_options.get.return_value = None
    
    result, total = get_joined_courses_by_user_id(mock_db, 999, 1, 10, '', True)
    
    assert result == []
    assert total == 0

# ---------- get_courses_by_teacher_id ----------
def test_get_courses_by_teacher_id_success(mock_db):
    fake_courses = [FakeCourse(), FakeCourse(id=2)]
    mock_query = Mock()
    mock_options = Mock()
    mock_filter = Mock()
    mock_count = Mock(return_value=2)
    mock_offset = Mock()
    mock_limit = Mock()
    mock_all = Mock(return_value=fake_courses)
    
    mock_db.query.return_value = mock_query
    mock_query.options.return_value = mock_options
    mock_options.filter.return_value = mock_filter
    mock_filter.count.return_value = 2
    mock_filter.offset.return_value = mock_offset
    mock_offset.limit.return_value = mock_limit
    mock_limit.all.return_value = fake_courses
    
    result, total = get_courses_by_teacher_id(mock_db, 1, 1, 10, '', True)
    
    assert result == fake_courses
    assert total == 2

# ---------- save_course ----------
def test_save_course_success(mock_db):
    fake_course = FakeCourse()
    mock_db.add = Mock()
    mock_db.commit = Mock()
    mock_db.refresh = Mock()
    
    result = save_course(mock_db, fake_course)
    
    assert result == fake_course
    mock_db.add.assert_called_once_with(fake_course)
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(fake_course)

# ---------- get_course_by_name ----------
def test_get_course_by_name_success(mock_db):
    fake_course = FakeCourse()
    mock_query = Mock()
    mock_filter = Mock()
    mock_first = Mock(return_value=fake_course)
    
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    mock_filter.first.return_value = fake_course
    
    result = get_course_by_name(mock_db, "Test Course")
    
    assert result == fake_course

def test_get_course_by_name_not_found(mock_db):
    mock_query = Mock()
    mock_filter = Mock()
    mock_first = Mock(return_value=None)
    
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    mock_filter.first.return_value = None
    
    result = get_course_by_name(mock_db, "Nonexistent Course")
    
    assert result is None

# ---------- dissolve_course ----------
def test_dissolve_course_success(mock_db):
    fake_course = FakeCourse(is_deleted=False)
    mock_db.commit = Mock()
    mock_db.refresh = Mock()
    
    result = dissolve_course(mock_db, fake_course)
    
    assert result == fake_course
    assert fake_course.is_deleted is True
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(fake_course) 

from sqlalchemy.sql.elements import BinaryExpression

def test_get_all_courses_include_dissolved_false(mock_db):
    fake_courses = [FakeCourse(), FakeCourse(id=2)]
    mock_query = Mock()
    mock_options = Mock()
    mock_options.filter.return_value = mock_options
    mock_options.offset.return_value = mock_options
    mock_options.limit.return_value = mock_options
    mock_options.count.return_value = 2
    mock_options.all.return_value = fake_courses

    mock_db.query.return_value = mock_query
    mock_query.options.return_value = mock_options

    result, total = get_all_courses(mock_db, 1, 10, '', False)

    assert result == fake_courses
    assert total == 2
    # 检查 filter 参数类型
    mock_options.filter.assert_called()
    args, kwargs = mock_options.filter.call_args
    assert isinstance(args[0], BinaryExpression)# 断言 filter(Course.is_deleted == False) 被调用

def test_get_courses_by_teacher_id_include_dissolved_false_and_keyword(mock_db):
    fake_courses = [FakeCourse()]

    # 设置 mock 链
    mock_query = Mock(name="query")
    mock_with_options = Mock(name="with_options")
    mock_filtered_by_teacher = Mock(name="filtered_by_teacher")
    mock_filtered_by_deleted = Mock(name="filtered_by_deleted")
    mock_filtered_by_keyword = Mock(name="filtered_by_keyword")

    # 设置链式调用返回值
    mock_db.query.return_value = mock_query
    mock_query.options.return_value = mock_with_options
    mock_with_options.filter.return_value = mock_filtered_by_teacher
    mock_filtered_by_teacher.filter.return_value = mock_filtered_by_deleted
    mock_filtered_by_deleted.filter.return_value = mock_filtered_by_keyword

    # 设置最终查询返回值
    mock_filtered_by_keyword.count.return_value = 1
    mock_filtered_by_keyword.offset.return_value = mock_filtered_by_keyword
    mock_filtered_by_keyword.limit.return_value = mock_filtered_by_keyword
    mock_filtered_by_keyword.all.return_value = fake_courses

    # 调用目标函数
    result, total = get_courses_by_teacher_id(
        mock_db, teacher_id=1, page=1, page_size=10, keyword='test', include_dissolved=False
    )

    # 验证
    assert result == fake_courses
    assert total == 1

def test_get_joined_courses_by_user_id_filter_and_keyword(mock_db):
    # 1个被过滤掉
    fake_user = FakeUser()
    fake_user.joined_courses = [
        FakeCourse(is_deleted=False, name="abc", teacher=FakeUser(username="t1")),
        FakeCourse(is_deleted=True, name="def", teacher=FakeUser(username="t2")),
        FakeCourse(is_deleted=False, name="hello", teacher=FakeUser(username="t3")),
    ]
    mock_query = Mock()
    mock_options = Mock()
    mock_get = Mock(return_value=fake_user)

    mock_db.query.return_value = mock_query
    mock_query.options.return_value = mock_options
    mock_options.get.return_value = fake_user

    # include_dissolved=False, keyword="hello"
    result, total = get_joined_courses_by_user_id(mock_db, 1, 1, 10, 'hello', False)
    # 只剩下 name="hello" 且 is_deleted=False 的那一个
    assert total == 1
    assert result[0].name == "hello"