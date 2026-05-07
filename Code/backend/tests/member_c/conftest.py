import json
import sys
import types
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.exceptions import HTTPException as StarletteHTTPException

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if "pymysql" not in sys.modules:
    fake_pymysql = types.ModuleType("pymysql")
    fake_pymysql.paramstyle = "pyformat"
    fake_pymysql.threadsafety = 1
    fake_pymysql.apilevel = "2.0"
    fake_pymysql.connect = lambda *args, **kwargs: None
    sys.modules["pymysql"] = fake_pymysql

if "gridfs" not in sys.modules:
    fake_gridfs = types.ModuleType("gridfs")

    class FakeGridFS:
        def __init__(self, db):
            self.db = db

    fake_gridfs.GridFS = FakeGridFS
    sys.modules["gridfs"] = fake_gridfs

if "bson" not in sys.modules:
    fake_bson = types.ModuleType("bson")
    fake_bson.ObjectId = lambda value: value
    sys.modules["bson"] = fake_bson

if "pymongo" not in sys.modules:
    fake_pymongo = types.ModuleType("pymongo")

    class FakeMongoClient:
        def __init__(self, uri):
            self.uri = uri

        def __getitem__(self, name):
            return {}

        def close(self):
            return None

    fake_pymongo.MongoClient = FakeMongoClient
    sys.modules["pymongo"] = fake_pymongo

from config.db import Base, get_db
from entity.Comment import Comment
from entity.Course import Course
from entity.Exercise import Exercise, ExerciseType
from entity.ExerciseSet import ExerciseSet
from entity.Post import Post
from entity.User import User
from entity.UserAuth import UserAuth
import controller.ExerciseController as ExerciseController
import controller.PostController as PostController
from service.UserService import get_current_user
from util.exception import http_exception_handler, validation_exception_handler


@pytest.fixture
def engine():
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=test_engine)
    try:
        yield test_engine
    finally:
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def session_factory(engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db_session(session_factory):
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_app(session_factory):
    app = FastAPI()
    app.include_router(PostController.router, prefix="/api/course")
    app.include_router(ExerciseController.router)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield app
    app.dependency_overrides.clear()


@pytest.fixture
def client(test_app):
    with TestClient(test_app) as test_client:
        yield test_client


@pytest.fixture
def login_as(test_app):
    def _login_as(user):
        test_app.dependency_overrides[get_current_user] = lambda: user

    yield _login_as
    test_app.dependency_overrides.pop(get_current_user, None)


def create_user(db_session, username, role, email=None, name=None):
    user = User(
        username=username,
        role=role,
        email=email or f"{username}@example.com",
        name=name or username,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def create_course(db_session, teacher, name="Software Testing", description="Course for tests"):
    course = Course(name=name, description=description, teacher_id=teacher.id, is_deleted=False)
    db_session.add(course)
    db_session.commit()
    db_session.refresh(course)
    return course


def create_exercise_set(
    db_session,
    course,
    title="线性代数练习一",
    description="测试习题集",
    document_id="doc-1",
    document_name="doc-A.pdf",
):
    exercise_set = ExerciseSet(
        course_id=course.id,
        title=title,
        description=description,
        document_id=document_id,
        document_name=document_name,
    )
    db_session.add(exercise_set)
    db_session.commit()
    db_session.refresh(exercise_set)
    return exercise_set


def create_exercise(db_session, exercise_set, question, exercise_type, options, answer):
    exercise = Exercise(
        exercise_set_id=exercise_set.id,
        question=question,
        type=exercise_type,
        options=json.dumps(options),
        answer=json.dumps(answer),
    )
    db_session.add(exercise)
    db_session.commit()
    db_session.refresh(exercise)
    return exercise


def create_post(
    db_session,
    course,
    user,
    title,
    content,
    is_anonymous=False,
    created_at=None,
):
    post = Post(
        course_id=course.id,
        user_id=user.id,
        title=title,
        content=content,
        is_anonymous=is_anonymous,
        created_at=created_at or datetime.utcnow(),
    )
    db_session.add(post)
    db_session.commit()
    db_session.refresh(post)
    return post


def create_comment(
    db_session,
    post,
    user,
    content,
    parent_id=None,
    is_anonymous=False,
    created_at=None,
):
    comment = Comment(
        post_id=post.id,
        user_id=user.id,
        content=content,
        parent_id=parent_id,
        is_anonymous=is_anonymous,
        created_at=created_at or datetime.utcnow(),
    )
    db_session.add(comment)
    db_session.commit()
    db_session.refresh(comment)
    return comment


@pytest.fixture
def teacher_user(db_session):
    return create_user(db_session, "teacher_user", "teacher")


@pytest.fixture
def student_user(db_session):
    return create_user(db_session, "student_user", "student")


@pytest.fixture
def course_1(db_session, teacher_user):
    return create_course(db_session, teacher_user)


@pytest.fixture
def exercise_set_1(db_session, course_1):
    return create_exercise_set(db_session, course_1)


@pytest.fixture
def exercise_bundle(db_session, exercise_set_1):
    single = create_exercise(
        db_session,
        exercise_set_1,
        "1 + 1 = ?",
        ExerciseType.single,
        ["1", "2", "3", "4"],
        "B",
    )
    multi = create_exercise(
        db_session,
        exercise_set_1,
        "哪些是质数？",
        ExerciseType.multiple,
        ["2", "3", "4", "6"],
        ["A", "B"],
    )
    blank = create_exercise(
        db_session,
        exercise_set_1,
        "软件测试的英文是？",
        ExerciseType.blank,
        [],
        ["software testing", "Software Testing"],
    )
    return {"single": single, "multiple": multi, "blank": blank}


@pytest.fixture
def post_bundle(db_session, course_1, teacher_user, student_user):
    older = datetime.utcnow() - timedelta(days=1)
    newer = datetime.utcnow()
    post_real = create_post(
        db_session,
        course_1,
        student_user,
        title="作业讨论帖",
        content="这里讨论第一次作业",
        is_anonymous=False,
        created_at=older,
    )
    post_anon = create_post(
        db_session,
        course_1,
        teacher_user,
        title="匿名答疑",
        content="这里回答作业问题",
        is_anonymous=True,
        created_at=newer,
    )
    parent = create_comment(
        db_session,
        post_real,
        student_user,
        content="这是一级评论",
        created_at=older,
    )
    reply = create_comment(
        db_session,
        post_real,
        teacher_user,
        content="这是回复评论",
        parent_id=parent.id,
        created_at=newer,
    )
    return {
        "post_real": post_real,
        "post_anon": post_anon,
        "comment_parent": parent,
        "comment_reply": reply,
    }
