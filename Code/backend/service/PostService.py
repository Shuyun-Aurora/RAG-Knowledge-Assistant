from datetime import datetime

from sqlalchemy.orm import Session

from repository.CommentRepository import get_comments_by_post, add_comment
from repository.PostRepository import get_posts_by_course_paginated, count_posts_by_course, create_post, get_post_by_id

def fetch_course_posts(db: Session, course_id: int, skip: int, limit: int, keyword: str = ""):
    posts = get_posts_by_course_paginated(db, course_id, skip, limit, keyword)
    total = count_posts_by_course(db, course_id, keyword)
    return {"posts": posts, "total": total}

def publish_post(db: Session, course_id: int, user_id: int, title: str, content: str, is_anonymous: bool):
    return create_post(db, course_id, user_id, title, content, is_anonymous)

def get_post_comments(db: Session, post_id: int, skip: int, limit: int):
    return get_comments_by_post(db, post_id, skip, limit)

def create_comment(db: Session, post_id: int, user_id: int, content: str, created_at: datetime, parent_id=None, is_anonymous: bool = False):
    return add_comment(db, post_id, user_id, content, created_at, parent_id, is_anonymous)

def fetch_post_by_id(db: Session, post_id: int):
    return get_post_by_id(db, post_id)
