import pytest
from unittest.mock import Mock
from sqlalchemy.orm import Session
from repository.ExerciseRepository import (
    save_exercise_set, save_exercise, search_exercise_sets_with_pagination,
    get_exercise_set_with_exercises, delete_exercise_set_by_id,
    find_exercises_by_document_names, update_exercise
)

class FakeExerciseSet:
    def __init__(self, id=1, course_id=1, title="Test Set", description="Test Description"):
        self.id = id
        self.course_id = course_id
        self.title = title
        self.description = description
        self.exercises = []

class FakeExercise:
    def __init__(self, id=1, exercise_set_id=1, question="Test Question", 
                 type="single", options='["A", "B"]', answer='"A"'):
        self.id = id
        self.exercise_set_id = exercise_set_id
        self.question = question
        self.type = type
        self.options = options
        self.answer = answer

@pytest.fixture
def mock_db():
    return Mock(spec=Session)

# ---------- save_exercise_set ----------
def test_save_exercise_set_success(mock_db):
    fake_exercise_set = FakeExerciseSet()
    mock_db.add = Mock()
    mock_db.commit = Mock()
    mock_db.refresh = Mock()
    
    result = save_exercise_set(mock_db, fake_exercise_set)
    
    assert result == fake_exercise_set
    mock_db.add.assert_called_once_with(fake_exercise_set)
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(fake_exercise_set)

# ---------- save_exercise ----------
def test_save_exercise_success(mock_db):
    fake_exercise = FakeExercise()
    mock_db.add = Mock()
    mock_db.commit = Mock()
    mock_db.refresh = Mock()
    
    result = save_exercise(mock_db, fake_exercise)
    
    assert result == fake_exercise
    mock_db.add.assert_called_once_with(fake_exercise)
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(fake_exercise)

# ---------- search_exercise_sets_with_pagination ----------
def test_search_exercise_sets_with_pagination_basic(mock_db):
    fake_sets = [FakeExerciseSet(), FakeExerciseSet(id=2)]
    mock_query = Mock()
    mock_filter = Mock()
    mock_count = Mock(return_value=2)
    mock_offset = Mock()
    mock_limit = Mock()
    mock_all = Mock(return_value=fake_sets)
    
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    mock_filter.count.return_value = 2
    mock_filter.offset.return_value = mock_offset
    mock_offset.limit.return_value = mock_limit
    mock_limit.all.return_value = fake_sets
    
    result, total = search_exercise_sets_with_pagination(mock_db, 1, None, 1, 10)
    
    assert result == fake_sets
    assert total == 2

def test_search_exercise_sets_with_pagination_with_keyword(mock_db):
    fake_sets = [FakeExerciseSet()]
    mock_query = Mock()
    mock_filter = Mock()
    mock_count = Mock(return_value=1)
    mock_offset = Mock()
    mock_limit = Mock()
    mock_all = Mock(return_value=fake_sets)
    
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    mock_filter.filter.return_value = mock_filter
    mock_filter.count.return_value = 1
    mock_filter.offset.return_value = mock_offset
    mock_offset.limit.return_value = mock_limit
    mock_limit.all.return_value = fake_sets
    
    result, total = search_exercise_sets_with_pagination(mock_db, 1, "test", 1, 10)
    
    assert result == fake_sets
    assert total == 1

# ---------- get_exercise_set_with_exercises ----------
def test_get_exercise_set_with_exercises_success(mock_db):
    fake_exercise_set = FakeExerciseSet()
    fake_exercise_set.exercises = [FakeExercise(), FakeExercise(id=2)]
    mock_query = Mock()
    mock_options = Mock()
    mock_filter = Mock()
    mock_first = Mock(return_value=fake_exercise_set)
    
    mock_db.query.return_value = mock_query
    mock_query.options.return_value = mock_options
    mock_options.filter.return_value = mock_filter
    mock_filter.first.return_value = fake_exercise_set
    
    result = get_exercise_set_with_exercises(mock_db, 1)
    
    assert result == fake_exercise_set
    assert len(result.exercises) == 2

def test_get_exercise_set_with_exercises_not_found(mock_db):
    mock_query = Mock()
    mock_options = Mock()
    mock_filter = Mock()
    mock_first = Mock(return_value=None)
    
    mock_db.query.return_value = mock_query
    mock_query.options.return_value = mock_options
    mock_options.filter.return_value = mock_filter
    mock_filter.first.return_value = None
    
    result = get_exercise_set_with_exercises(mock_db, 999)
    
    assert result is None

# ---------- delete_exercise_set_by_id ----------
def test_delete_exercise_set_by_id_success(mock_db):
    fake_exercise_set = FakeExerciseSet()
    mock_query = Mock()
    mock_filter = Mock()
    mock_first = Mock(return_value=fake_exercise_set)
    mock_db.delete = Mock()
    mock_db.commit = Mock()
    
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    mock_filter.first.return_value = fake_exercise_set
    
    result = delete_exercise_set_by_id(mock_db, 1)
    
    assert result is True
    mock_db.delete.assert_called_once_with(fake_exercise_set)
    mock_db.commit.assert_called_once()

def test_delete_exercise_set_by_id_not_found(mock_db):
    mock_query = Mock()
    mock_filter = Mock()
    mock_first = Mock(return_value=None)
    
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    mock_filter.first.return_value = None
    
    result = delete_exercise_set_by_id(mock_db, 999)
    
    assert result is False

# ---------- find_exercises_by_document_names ----------
def test_find_exercises_by_document_names_success(mock_db):
    fake_exercises = [FakeExercise(), FakeExercise(id=2)]
    mock_query = Mock()
    mock_join = Mock()
    mock_filter = Mock()
    mock_all = Mock(return_value=fake_exercises)
    
    mock_db.query.return_value = mock_query
    mock_query.join.return_value = mock_join
    mock_join.filter.return_value = mock_filter
    mock_filter.all.return_value = fake_exercises
    
    result = find_exercises_by_document_names(mock_db, ["doc1.pdf", "doc2.pdf"])
    
    assert result == fake_exercises

def test_find_exercises_by_document_names_empty(mock_db):
    mock_query = Mock()
    mock_join = Mock()
    mock_filter = Mock()
    mock_all = Mock(return_value=[])
    
    mock_db.query.return_value = mock_query
    mock_query.join.return_value = mock_join
    mock_join.filter.return_value = mock_filter
    mock_filter.all.return_value = []
    
    result = find_exercises_by_document_names(mock_db, ["nonexistent.pdf"])
    
    assert result == []

# ---------- update_exercise ----------
def test_update_exercise_success(mock_db):
    fake_exercise = FakeExercise()
    mock_query = Mock()
    mock_filter = Mock()
    mock_first = Mock(return_value=fake_exercise)
    mock_db.commit = Mock()
    mock_db.refresh = Mock()
    
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    mock_filter.first.return_value = fake_exercise
    
    result = update_exercise(mock_db, 1, "New Question", "New Answer")
    
    assert result == fake_exercise
    assert fake_exercise.question == "New Question"
    assert fake_exercise.answer == "New Answer"
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(fake_exercise)

def test_update_exercise_not_found(mock_db):
    mock_query = Mock()
    mock_filter = Mock()
    mock_first = Mock(return_value=None)
    
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    mock_filter.first.return_value = None
    
    with pytest.raises(Exception, match="习题不存在"):
        update_exercise(mock_db, 999, "New Question", "New Answer") 