from sqlalchemy.orm import Session
from entity.Post import Post
from datetime import datetime

def get_posts_by_course_paginated(db: Session, course_id: int, skip: int = 0, limit: int = 10, keyword=""):
    query = db.query(Post).filter(Post.course_id == course_id)
    if keyword:
        query = query.filter(
            Post.title.ilike(f"%{keyword}%") | Post.content.ilike(f"%{keyword}%")
        )
    return query.order_by(Post.created_at.desc()).offset(skip).limit(limit).all()

def count_posts_by_course(db: Session, course_id: int, keyword=""):
    query = db.query(Post).filter(Post.course_id == course_id)
    if keyword:
        query = query.filter(
            Post.title.ilike(f"%{keyword}%") | Post.content.ilike(f"%{keyword}%")
        )
    return query.count()

def create_post(db: Session, course_id: int, user_id: int, title: str, content: str, is_anonymous: bool):
    post = Post(
        course_id=course_id,
        user_id=user_id,
        title=title,
        content=content,
        is_anonymous=is_anonymous,
        created_at=datetime.utcnow()
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post

def get_post_by_id(db: Session, post_id: int) -> Post | None:
    return db.query(Post).filter(Post.id == post_id).first()
